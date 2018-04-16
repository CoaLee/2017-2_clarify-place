#include<cstdio>
#include<iostream>
#include<algorithm>
#include<map>
#include<set>
#include<queue>
#include<vector>
#include<functional>
#include<string>
#include<string.h>
#include<stdlib.h>
#include<cmath>
#include<numeric>
#include<assert.h>
#include<stack>
#include<list>
#include<sstream>

using namespace std;

#define PI 3.14159265358979323846
#define ll long long
#define X first
#define Y second
#define pi pair<int,int>
#define pd pair<double,double>
#define vi vector<int>
#define vvi vector<vi>
#define sz(a) ((int)(a).size())
#define INF 1000000021
#define MOD 1000000007
#define N 200002


char c[100002];
char s[10002];
//char cmpstr[12] = "tab.m.all";

vector<string> db;
int cnt;

int main() {
	
	freopen("sr-20171108.txt", "r", stdin);

	db.reserve(10000);
	
	while (scanf("%s", c) != EOF) {
		if (strcmp(c,"tab.m.all")==0) {
			scanf("%s", s);
			db.push_back(s);
			++cnt;
		}
	}
	
	freopen("output.txt", "w", stdout);
	printf("cnt : %d\n", cnt);

	sort(db.begin(), db.end());
	int num = 0;
	int CODE1 = 1;
	int CODE2 = 1;

	vector<pair<int, string> > db_cnt;

	for (int i = 0; i < db.size(); ++i) {
		if (i>1 && db[i - 1].compare(db[i]) != 0) {
			if (CODE1 == 1)
				cout << db[i-1] << '\t' << num << '\n';
			if (CODE2 == 1)
				db_cnt.push_back(make_pair(num, db[i - 1]));
			num = 1;
		}
		else {
			++num;
		}
	}
	if (CODE1 == 1)
		cout << db[db.size() - 1] << '\t' << num << '\n';
	if (CODE2 == 1) {
		db_cnt.push_back(make_pair(num, db[db.size() - 1]));
		sort(db_cnt.begin(), db_cnt.end());
		for (int i = db_cnt.size() - 1; i >= 0; i--) {
			cout << db_cnt[i].second << '\t' << db_cnt[i].first << '\n';
		}
	}
	return 0;
}