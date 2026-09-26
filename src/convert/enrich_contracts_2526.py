import csv, io, json, re, unicodedata, urllib.request
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'FM26_5LEAGUE_PLAYERS_RAW.csv'
OUT = ROOT / 'data' / 'processed'
SEASON_URL = 'https://raw.githubusercontent.com/m-mahadi/top5-football-dataset/master/data/master/player_seasons.csv'
TM_BASE = 'https://raw.githubusercontent.com/eordo/transfermarkt-data/master/'
TM_FILES = ['premier_league/2025.csv','la_liga/2025.csv','bundesliga/2025.csv','serie_a/2025.csv','ligue_1/2025.csv']

def norm(x):
    x = '' if x is None else str(x)
    x = unicodedata.normalize('NFKD', x).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','',x)

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'FM26-Database/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode('utf-8-sig')

def fnum(x):
    if x in ('',None): return None
    try: return float(str(x).replace(',','').replace('€','').strip())
    except Exception: return None

def first(row,*keys):
    for k in keys:
        v = row.get(k)
        if v not in ('',None): return v
    return None

if not RAW.exists(): raise SystemExit(f'Missing source file: {RAW}')
players = list(csv.DictReader(RAW.open(encoding='utf-8-sig',newline='')))
master = list(csv.DictReader(io.StringIO(get(SEASON_URL))))
master = [r for r in master if r.get('season_label') == '2025/26']
by_key = {}
for r in master:
    key=(norm(r.get('player')),norm(r.get('team')))
    if key[0]: by_key[key]=r

transfers=[]
for filename in TM_FILES:
    try: transfers.extend(csv.DictReader(io.StringIO(get(TM_BASE+filename))))
    except Exception as exc: print('transfer source skipped:',filename,exc)
by_name={}
for r in transfers: by_name.setdefault(norm(r.get('player_name')),[]).append(r)

contracts=[]; loans=[]; loan_count_by_player={}
for p in players:
    name=p.get('name',''); club=p.get('club_canonical') or p.get('club','')
    r=by_key.get((norm(name),norm(club)))
    contract_start=first(r or {},'fifa_contract_start')
    contract_end=first(r or {},'fifa_contract_end')
    wage=fnum(first(r or {},'fifa_wage_eur'))
    release=fnum(first(r or {},'fifa_release_clause_eur'))
    value=fnum(first(r or {},'fifa_value_eur'))
    years=None
    if contract_start and contract_end:
        try: years=round((date.fromisoformat(str(contract_end)[:10])-date.fromisoformat(str(contract_start)[:10])).days/365.25,2)
        except Exception: pass
    contracts.append({'source_uid':p.get('_source_uid'),'name':name,'club':club,'league':p.get('league'),'season':'2025/26','contract_start':contract_start,'contract_end':contract_end,'contract_years':years,'wage_eur':wage,'wage_period':'year','release_clause_eur':release,'transfer_value_eur':value,'verification_status':'verified' if r else 'pending_external_verification','source_contract':'m-mahadi/top5-football-dataset (SoFIFA)' if r else None})
    own=[]
    for t in by_name.get(norm(name),[]):
        if str(t.get('is_loan','')).lower() not in ('1','true','yes'): continue
        row={'source_uid':p.get('_source_uid'),'name':name,'season':'2025/26','loan_club':t.get('club'),'parent_club':t.get('dealing_club'),'transfer_fee_eur':fnum(t.get('fee')),'is_loan':True,'option_to_buy':None,'option_fee_eur':None,'obligation_to_buy':None,'obligation_fee_eur':None,'verification_status':'verified_loan','source_transfer':'eordo/transfermarkt-data'}
        loans.append(row); own.append(row)
    loan_count_by_player[p.get('_source_uid')]=len(own)

OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'contracts_2526.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(contracts[0].keys())); w.writeheader(); w.writerows(contracts)
with (OUT/'loans_2526.json').open('w',encoding='utf-8') as f: json.dump(loans,f,ensure_ascii=False,indent=2)
audit={'season':'2025/26','players':len(players),'contract_matches':sum(x['verification_status']=='verified' for x in contracts),'loan_players':sum(v>0 for v in loan_count_by_player.values()),'loan_records':len(loans),'option_to_buy_verified':0,'obligation_to_buy_verified':0,'note':'Options/obligations remain null unless explicitly present in the source datasets; no values are invented.'}
with (OUT/'contract_loan_audit_2526.json').open('w',encoding='utf-8') as f: json.dump(audit,f,ensure_ascii=False,indent=2)
print(json.dumps(audit,ensure_ascii=False))
