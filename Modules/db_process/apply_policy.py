import mysql_interact as dbi # db i(nterface)
import urllib.parse

"""
'apply_policy'
    1. apply policies to determine the intent of searches.
    2. if logs are too big, proceed it with chopping them into chunks.
    3. policy list:
        i)   policy_region_words: 
        ii)  policy_store_actions:
        iii) policy_flick_click:
        ...
"""

DB_UPDATING = True

# global variable
whole_store_ids = {'keywords': [], 'ids': []}
whole_flick_ids = {'keywords': [], 'ids': []}

# load crawled data from a file
def load_crawled_ids(varname, fname, delim='\t'):
    with open('../../Data Parsing/{}'.format(fname), 'r') as crawl_file:
        raw_lines = crawl_file.readlines()
        lines = [line.strip().split() for line in raw_lines]
        keywords = []
        ids = []
        i = 0
        for line in lines:
            keywords.append(line[0])
            ids.append(line[2:])
            i += 1
        varname['keywords'] = keywords
        varname['ids'] = ids

# attach the last action of a session to it
def execute_policies():
    dbi.init_db_conn()

    chopped_index = dbi.chop_pos['search']
    searches = dbi.select_columns_where(\
            'search', columns=['id', 'session_id', 'keyword'], chopping=True)
    sessions = [search[1] for search in searches]
    matched_index = -1

    prev_action = dbi.select_columns_where('action', where='id = {}'.format(dbi.chop_pos['action']))[0]
    surplus_actions = ()    # actions left after splitting. 
    is_action_collected = False

    # 'unmatched' variables: to tolerate some bad-positioned log.
    # ex) some sessions appear at < 100 from click_log, > 1000000 from search_log.
    unmatched_actionss = []
    unmatched_cnt = 0
    unmatched_BUF = 10
    matching_STEP = dbi.SELECT_CHOP_SIZE // unmatched_BUF

    while True:
        # action: (id, session_id, date_text, action_type, url)
        actions = dbi.select_columns_where('action', chopping=True)
        if actions == () or searches == ():     # passed the last item
            break

        # if there were unmatched_actionss getting stacked during prev loop, add them first.
        # action'ss': list of list of action
        actionss_splitted = [] if unmatched_cnt == 0 else unmatched_actionss[-unmatched_cnt:]
        unmatched_cnt = 0

        # split actions by session
        session_changing_pos = []
        i = 0
        for action in actions:
            if prev_action[1] != action[1]:
                prev_action = action
                session_changing_pos.append(i)
            i += 1

        actionss_splitted.append(surplus_actions + actions[:session_changing_pos[0]])
        i = 1   # 0 idx is used with surplus actions above
        while i < len(session_changing_pos):
            actionss_splitted.append(actions[session_changing_pos[i-1]:session_changing_pos[i]])
            i += 1
        surplus_actions = actions[session_changing_pos[i-1]:]

        # i-indexing is used to jump back.
        i = 0
        while i < len(actionss_splitted):
            actions_splitted = actionss_splitted[i]
            cur_session = actions_splitted[0][1]

            if cur_session not in sessions:
                unmatched_cnt += 1
                if unmatched_cnt < unmatched_BUF:
                    #print('unmatched action. id: {}  |  session_id:  {}'\
                    #        .format(actions_splitted[-1][0], actions_splitted[-1][1]))
                    unmatched_actionss.append(actions_splitted)
                    i += 1
                    continue
                # if the number of consecutive unmatching gets over BUF, request a new chopped searches.
                else : 
                    matched_steps = matched_index // matching_STEP  # steps : 0 ~ (BUF-1), -1: unmatched
                    i = i - matched_steps
                    if matched_steps >= 0 :
                        unmatched_actionss = unmatched_actionss[:-matched_steps-1]
                    unmatched_cnt = 0

                    chopped_index += matched_index + 1
                    dbi.rewind_select('search', chopped_index)
                    searches = dbi.select_columns_where(\
                            'search', columns=['id', 'session_id', 'keyword'], chopping=True)
                    sessions = [search[1] for search in searches]
                    matched_index = -1
                    continue

            matched_index = sessions.index(cur_session)
            matched_search = searches[matched_index]    # currently, search: [id, session_id]
            print('\n >>> m_search: {}, len_actions {}, m_index: {}'\
                    .format(matched_search, len(actions_splitted), matched_index))

            (F_action, F_naver) = calculate_policies(matched_search, actions_splitted)
            find_coordinates(matched_search, actions_splitted)

            if DB_UPDATING is True:
                if F_action != -1:
                    dbi.update_datum_where('search', ['F_action', '{}'.format(F_action)], \
                            where='id="{}"'.format(matched_search[0]))
                if F_naver != -1:
                    dbi.update_datum_where('search', ['F_naver', '{}'.format(F_naver)], \
                            where='id="{}"'.format(matched_search[0]))

            unmatched_cnt = 0
            i += 1

    dbi.exit_db_conn()

def calculate_policies(search, actions):
    # policy_att(search, actions)
    F = policy_region_words(search, actions)
    if F[0] == 0:
        return F

    F = policy_otregion(search, actions)
    if F[0] == 1:
        return F
    
    F = policy_att(search, actions)
    if F[0] == 1:
        return F

    F = policy_lpa(search, actions)
    if F[0] == 1:
        return F

    F = policy_flick_click(search, actions)
    return F

special_region_words = ['맛집', '추천']
def policy_region_words(search, actions):
    keyword = search[2].replace(' ', '')
    for word in special_region_words:
        if word in keyword:
            return (0, 0)
    return (-1, -1)

special_store_actions = ['otregion'] #, 'lpa'] #, 'att']
def policy_store_actions(search, actions):
    for store_action_string in special_store_actions:
        for action in actions:
            if store_action_string in action[3]:
                return (1, 1)
    return (-1, -1)

otregion_string = 'otregion'
def policy_otregion(search, actions):
    for action in actions:
        if otregion_string in action[3]:
            if DB_UPDATING is True:
                dbi.update_datum_where('search', ['otregion', '1'], where='id="{}"'.format(search[0]))
            return (1, 1)
    return (-1, -1)

att_string = 'att'
def policy_att(search, actions):
    for action in actions:
        if att_string in action[3]:
            if DB_UPDATING is True:
                dbi.update_datum_where('search', ['att', '1'], where='id="{}"'.format(search[0]))
            return (1, 1)
    return (-1, -1)
            
att_string = 'lpa'
def policy_lpa(search, actions):
    for action in actions:
        if att_string in action[3]:
            if DB_UPDATING is True:
                dbi.update_datum_where('search', ['lpa', '1'], where='id="{}"'.format(search[0]))
            return (1, 1)
    return (-1, -1)

flick_string = 'resultflick'
click_string = 'result'
# search: (id, session_id, keyword)
# actions: ((id, session_id, date_text, action_type, res_ids, keyword, res_row, url), ...)
def policy_flick_click(search, actions):
    num_flick_region = 0
    num_flick_store = 0
    num_click_region = 0
    num_click_store = 0
    is_store_last_clicked = -1  # -1: not clicked, 0: region, 1: store

    keyword = search[2].replace(' ', '')    # remove spaces
    keywords = whole_store_ids['keywords']
    if keyword not in keywords:
        # print('keyword not found')
        return (-1, -1)
    keyword_idx = keywords.index(keyword)
    store_ids = whole_store_ids['ids'][keyword_idx]
    ids_first_page = whole_flick_ids['ids'][keyword_idx][:3]
    cnt_first_page = len(ids_first_page)

    cnt_first_page_store = 0
    for one_id in ids_first_page:
        if one_id in store_ids:
            cnt_first_page_store += 1
    
    try:
        F_naver = cnt_first_page_store / cnt_first_page
    except ZeroDivisionError:
        # print(search)
        # print('zeroDivision! action: {}'.format(actions[0][2:4]))
        F_naver = 0
    
    ## COUNTING PROCEDURE ##
    cur_row = 1
    ids_flicked = ids_first_page
    ids_clicked = []
    for action in actions:
        # print(action)
        if flick_string in action[3]:   # *.resultflick
            if int(action[6]) == 1:
                ids_flicked[:3] = action[4].split('/')
            if int(action[6]) > cur_row:
                cur_row += 1
                ids_flicked += action[4].split('/')
        elif click_string in action[3]: # *.result, *.resultimg
            clicked_id = action[4]
            if clicked_id in ids_flicked:
                ids_flicked.remove(clicked_id)
            ids_clicked.append(clicked_id)
            
    # print(keyword, 'ids_flicked: ', ids_flicked)
    # print(keyword, 'ids_clicked: ', ids_clicked)
    
    num_flick_region = len(ids_flicked)
    for one_id in ids_flicked:
        if one_id in store_ids:
            num_flick_store += 1
    num_flick_region -= num_flick_store
    
    num_click_region = len(ids_clicked)
    for one_id in ids_clicked:
        if one_id in store_ids:
            num_click_store += 1
    num_click_region -= num_click_store

    print('nfr: {}  | nfs: {}  | ncr: {}  | ncs: {} '\
            .format(num_flick_region, num_flick_store, num_click_region, num_click_store))
        
    last_action = actions[-1]
    if last_action[-1] != '' and click_string in last_action[3]:
        parsed_url = urllib.parse.unquote(urllib.parse.unquote(last_action[-1]))
        tmp_splitted = parsed_url.split('?id=')
        if len(tmp_splitted) > 1:
            clicked_id = tmp_splitted[1].split('&')[0] 
            is_store_last_clicked = 1 if clicked_id in store_ids else 0
            print('last_clicked_id: {}  | is_store : {}'.format(clicked_id, is_store_last_clicked))

    sum_flick = num_flick_store + num_flick_region
    sum_click = num_click_store + num_click_region
    ratio_flick = 0.191 if sum_flick > 0 else 0
    ratio_click = 0.809 if sum_click > 0 else 0
    sum_ratio = ratio_flick + ratio_click
    if sum_ratio == 0:
        return (-1, -1)
    weight_flick = ratio_flick / sum_ratio
    weight_click = ratio_click / sum_ratio
    weight_last = 2 if is_store_last_clicked >= 0 else 0

    F_flick = weight_flick * num_flick_region/sum_flick if sum_flick > 0 else 0
    f_last = weight_last if is_store_last_clicked == 1 else 0
    F_click = weight_click * (num_click_store + f_last) / (sum_click + f_last) if sum_click > 0 else 0

    F_action = F_flick + F_click

    print('wf: {}  | wc: {}  | wl : {}\nFf: {}  | Fc: {}  | Fl: {}'\
            .format(weight_flick, weight_click, weight_last, F_flick, F_click, f_last))

    return (F_action, F_naver)

def find_coordinates(search, actions):
    for action in actions:
        url = action[-1]
        if url != '':
            x_idx = url.find('%26x%3D')
            if x_idx != -1:
                url = url[x_idx+3:]
                y_idx = url.find('%26y%3D')
                x = url[4:y_idx]
                url = url[y_idx+3:]
                z_idx = url.find('%26')
                y = url[4:z_idx]
                print('x: {}  |  y: {}'.format(x, y))
                if DB_UPDATING is True:
                    dbi.update_datum_where('search', ['coord_x', '{}'.format(x)], where='id="{}"'.format(search[0]))
                    dbi.update_datum_where('search', ['coord_y', '{}'.format(y)], where='id="{}"'.format(search[0]))

def main():
    load_crawled_ids(whole_store_ids, 'crawled_store_ids.txt', delim=' ')
    load_crawled_ids(whole_flick_ids, 'crawled_flick_ids.txt', delim=' ')
    execute_policies()

if __name__ == '__main__':
    main()
