import argparse
import json
from .index import ingest_folder, search, stats
from .settings import LIBRARY_ROOT

def main():
    p=argparse.ArgumentParser(prog="vault");s=p.add_subparsers(dest="command",required=True)
    i=s.add_parser("ingest");i.add_argument("path",nargs="?",default=str(LIBRARY_ROOT))
    q=s.add_parser("search");q.add_argument("query");q.add_argument("--limit",type=int,default=8)
    s.add_parser("stats");args=p.parse_args()
    if args.command=="ingest": print(json.dumps(ingest_folder(args.path),indent=2))
    elif args.command=="search": print(json.dumps(search(args.query,args.limit),indent=2,ensure_ascii=False))
    else: print(json.dumps(stats(),indent=2))

if __name__=="__main__":main()
