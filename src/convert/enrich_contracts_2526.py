import csv, io, json, re, unicodedata, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/FM26_5LEAGUE_PLAYERS_RAW.csv'
OUT=ROOT/'data/processed'
SEASON_URL='https://raw.githubusercontent.com/m-mahadi/top5-football-dataset/master/data/master/player_seasons.csv'
TM='https://raw.githubusercontent.com/eordo/transfermarkt-data/master/'
FILES=['premier_league/2025.csv','la_liga/2025.csv','bundesliga/2025.csv','serie_a/2025.csv','ligue_1/2025.csv']
def norm(x):
 x='' if x is None else str(x); x=unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower(); return re.sub(r'[^a-z0-9]+','',x)
def get(url):
 r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FM26-Database/1.0'}),timeout=90); return r.read().decode('utf-8-sig')
def fnum(x):
 try:return float(x) if x not in ('',None) else None
 except:return None
if not RAW.exists(): raise SystemExit(f'Missing {RAW}; upload the supplied 4,313-player CSV to data/raw first.')
players=list(csv.DictReader(RAW.open(encoding='utf-8-sig',newline='')))
master=list(csv.DictReader(io.StringIO(get(SEASON_URL))))
master=[r for r in master if r.get('season_label')=='2025/26']
bykey={}
for r in master:
 k=(norm(r.get('player')),norm(r.get('team')))
 if k[0] and (k not in bykey or r.get('fifa_contract_end')): bykey[k]=r
trans=[]
for p in FILES:
 try: trans+=list(csv.DictReader(io.StringIO(get(TM+p))))
 except Exception: pass
byname={}
for r in trans: byname.setdefault(norm(r.get('player_name')),[]).append(r)
contracts=[]; loans=[]; audit=[]
for p in players:
 name=p.get('name',''); club=p.get('club_canonical') or p.get('club',''); r=bykey.get((norm(name),norm(club)))
 c={'source_uid':p.get('_source_uid'),'name':name,'club':club,'league':p.get('league'),'season':'2025/26','contract_start':None,'contract_end':None,'contract_years':None,'wage_eur':None,'release_clause_eur':None,'transfer_value_eur':None,'verification_status':'unmatched','source_contract':None}
 if r:
  c.update(contract_start=r.get('fifa_contract_start') or None,contract_end=r.get('fifa_contract_end') or None,wage_eur=fnum(r.get('fifa_wage_eur')),release_clause_eur=fnum(r.get('fifa_release_clause_eur')),transfer_value_eur=fnum(r.get('fifa_value_eur')),verification_status='matched_contract_source',source_contract='m-mahadi/top5-football-dataset (SoFIFA)')
  try:c['contract_years']=int(float(c['contract_end']))-int(float(c['contract_start'])) if c['contract_start'] and c['contract_end'] else None
  except:pass
 contracts.append(c)
 for t in byname.get(norm(name),[]):
  if str(t.get('is_loan','')).lower() in ('1','true'):
   loans.append({'source_uid':p.get('_source_uid'),'name':name,'season':'2025/26','loan_club':t.get('club'),'parent_club':t.get('dealing_club'),'transfer_fee_eur':fnum(t.get('fee')),'is_loan':True,'option_to_buy':None,'option_fee_eur':None,'obligation_to_buy':None,'obligation_fee_eur':None,'verification_status':'loan_source_match','source_transfer':'eordo/transfermarkt-data'})
 audit.append({'source_uid':p.get('_source_uid'),'name':name,'contract_matched':bool(r),'loan_records':len(loans)})
OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'contracts_2526.csv').open('w',encoding='utf-8-sig',newline='') as f: w=csv.DictWriter(f,fieldnames=contracts[0].keys()); w.writeheader(); w.writerows(contracts)
with (OUT/'loans_2526.json').open('w',encoding='utf-8') as f: json.dump(loans,f,ensure_ascii=False,indent=2)
with (OUT/'contract_loan_audit_2526.json').open('w',encoding='utf-8') as f: json.dump({'players':len(players),'contract_matches':sum(x['verification_status']=='matched_contract_source' for x in contracts),'loan_records':len(loans),'audit':audit},f,ensure_ascii=False,indent=2)
print('processed',len(players),'players; contract matches',sum(x['verification_status']=='matched_contract_source' for x in contracts),'loan records',len(loans))
