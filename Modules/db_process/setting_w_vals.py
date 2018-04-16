import math

def calc_f_by_action(num_flick_region, num_flick_store, num_click_region, num_click_store, last_clicked, weight_flick, weight_click, weight_last):
    sum_flick = num_flick_store + num_flick_region
    sum_click = num_click_store + num_click_region
    ratio_flick = weight_flick if sum_flick > 0 else 0
    ratio_click = weight_click if sum_click > 0 else 0
    ratio_last = weight_last if last_clicked > 0 else 0
    sum_ratio = ratio_flick + ratio_click + ratio_last

    weight_flick = ratio_flick / sum_ratio
    weight_click = ratio_click / sum_ratio
    weight_last = ratio_last / sum_ratio

    F_flick = weight_flick * num_flick_region/sum_flick if sum_flick > 0 else 0
    f_last = weight_last if last_clicked == 1 else 0
    F_click = (weight_click * num_click_store + f_last) / (sum_click + f_last) if sum_click > 0 else 0

    F_action = F_flick + F_click
    
    return F_action

def calc_f_dist(wf, wc, wl):
    f_by_human_list = data_dict['f_by_human']
    last_click_list = data_dict['last_click']
    nfr_list = data_dict['nfr']
    nfs_list = data_dict['nfs']
    ncr_list = data_dict['ncr']
    ncs_list = data_dict['ncs']

    f_sum = 0
    f_dist = 0
    i = 0
    while i < len(nfr_list):
        f_by_action = calc_f_by_action(nfr_list[i], nfs_list[i], ncr_list[i], ncs_list[i], last_click_list[i], wf, wc, wl)
        tmp_f_dist = pow(f_by_human_list[i] - f_by_action, 2)
        f_sum += tmp_f_dist
        i += 1

    f_dist = f_sum / len(nfr_list)

    return f_dist

def calc_f_possibility(wf, wc, wl):
    f_by_human_list = data_dict['f_by_human']
    last_click_list = data_dict['last_click']
    nfr_list = data_dict['nfr']
    nfs_list = data_dict['nfs']
    ncr_list = data_dict['ncr']
    ncs_list = data_dict['ncs']

    i = 0
    res = 0
    cnt_calculated = 0
    while i < len(nfr_list):
        F = f_by_human_list[i]
        G = calc_f_by_action(nfr_list[i], nfs_list[i], ncr_list[i], ncs_list[i], last_click_list[i], wf, wc, wl)
        tmp = F * math.log(G) + (1-F) * math.log(1-G)
        # print('F: {}  | G: {}  | val: {}'.format(F, G, tmp))
        res += tmp
        cnt_calculated += 1
        i += 1

    return - res / cnt_calculated

data_dict = {}
data_dict['word'] = []
data_dict['f_by_human'] = []
data_dict['last_click'] = []
data_dict['nfr'] = []
data_dict['nfs'] = []
data_dict['ncr'] = []
data_dict['ncs'] = []

with open('F_human.txt', 'r') as raw_file:
    for line in raw_file:
        [word, f_by_human, last_click, nfr, nfs, ncr, ncs] = line.strip().split(' ')
        data_dict['word'].append(word)
        data_dict['f_by_human'].append(int(f_by_human))
        data_dict['last_click'].append(int(last_click))
        data_dict['nfr'].append(int(nfr))
        data_dict['nfs'].append(int(nfs))
        data_dict['ncr'].append(int(ncr))
        data_dict['ncs'].append(int(ncs))

wf_list = []
wc_list = []
wl_list = []
f_poss_list = []
f_dist_list = []

for wf in range(1, 101, 1):
    wf /= 100
    wc = 1 - wf
    for wl in range(1, 11, 1):
        wf_list.append(wf)
        wc_list.append(wc)
        wl_list.append(wl)
        f_poss = calc_f_possibility(wf, wc, wl)
        f_poss_list.append(f_poss)
        f_dist = calc_f_dist(wf, wc, wl)
        f_dist_list.append(f_dist)
        print('{} {} {} {} {}'.format(wf, wc, wl, f_poss, f_dist))

min_val = min(f_poss_list)
min_idx = f_poss_list.index(min_val)

print('\nwf: {}  | wc: {}  | wl: {}  | f_poss: {}\n'.\
        format(wf_list[min_idx], wc_list[min_idx], wl_list[min_idx], f_poss_list[min_idx]))

min_val = min(f_dist_list)
min_idx = f_dist_list.index(min_val)

# print('\nwf: {}  | wc: {}  | wl: {}  | f_dist: {}\n'.\
#        format(wf_list[min_idx], wc_list[min_idx], wl_list[min_idx], f_dist_list[min_idx]))
