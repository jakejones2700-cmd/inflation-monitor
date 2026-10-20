#!/usr/bin/env python3
"""Refresh official CPI headline/core and PCE Table 2.8.7 series.

Do not silently roll over detailed CPI contribution categories when only aggregate
headline/core have updated. BEA API key is optional but required for PCE refresh.
"""
import csv, io, json, os, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime
P=Path(__file__).parent
J=P/"data/dashboard.json"
data=json.loads(J.read_text())
def fetch(url, params=None):
    if params: url += ("&" if "?" in url else "?")+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"InflationMonitor/1.0 contact via GitHub"})
    with urllib.request.urlopen(req,timeout=35) as r: return json.load(r)
def pct(a,b):return round(100*(a/b-1),4) if b else None
def update_cpi():
    try:
        obj=fetch("https://api.bls.gov/publicAPI/v2/timeseries/data/",{"seriesid":"CUSR0000SA0,CUSR0000SA0L1E","startyear":str(datetime.now().year-3),"endyear":str(datetime.now().year)})
        if obj.get("status")!="REQUEST_SUCCEEDED":raise RuntimeError(str(obj.get("message")))
        found={}
        for series in obj["Results"]["series"]:
            rows={}
            for x in series["data"]:
                if x["period"].startswith("M") and x["period"]!="M13":
                    ym=x["year"]+"-"+x["period"][1:];rows[ym]=float(x["value"])
            found[series["seriesID"]]=rows
        for sid,basket in [("CUSR0000SA0","headline"),("CUSR0000SA0L1E","core")]:
            rows=found[sid]
            for ym,level in rows.items():
                year,month=map(int,ym.split("-"))
                prev=f"{year-1}-{month:02d}"
                pmonth=f"{year-1}-12" if month==1 else f"{year}-{month-1:02d}"
                if prev not in rows or pmonth not in rows:continue
                entry=data["cpi"]["months"].setdefault(ym,{"headline":{},"core":{}})[basket]
                entry["yoy"]=pct(level,rows[prev]);entry["mom"]=pct(level,rows[pmonth])
                if "items" not in entry:
                    entry["items"]=[]
                    entry["warning"]="Official seasonally adjusted index-derived aggregate rates; category contribution data not yet available for this period."
        data["cpi"]["note"]="CPI totals calculated from BLS seasonally adjusted index levels. Category data are seeded estimates for September 2026 only."
        print("CPI refreshed")
    except Exception as ex:print("CPI refresh unavailable:",ex)
def update_pce():
    key=os.getenv("BEA_API_KEY","").strip()
    if not key:print("No BEA_API_KEY; retaining embedded PCE sample");return
    try:
        raw=fetch("https://apps.bea.gov/api/data",{"UserID":key,"method":"GetData","datasetname":"NIPA","TableName":"T20807","Frequency":"M","Year":"ALL","ResultFormat":"JSON"})
        root=raw.get("BEAAPI",{})
        rows=root.get("Results",{}).get("Data",[])
        if not isinstance(rows,list) or not rows:raise ValueError(str(root.get("Error") or "No NIPA rows returned"))
        byperiod={}
        for r in rows:
            period=str(r.get("TimePeriod",""))
            if len(period)!=7 or "M" not in period:continue
            year,month=period.split("M")
            if not (year.isdigit() and month.isdigit()):continue
            ym=year+"-"+month.zfill(2)
            rawv=str(r.get("DataValue","")).replace(",","").strip()
            try:v=float(rawv)
            except ValueError:continue
            code=str(r.get("LineNumber","")).strip()
            if not code.isdigit():continue
            byperiod.setdefault(ym,{})[int(code)]={"mom":v,"name":str(r.get("LineDescription") or r.get("Line") or "").strip()}
        for ym,lines in sorted(byperiod.items()):
            if 1 not in lines:continue
            dst=data["pce"]["months"].setdefault(ym,{"headline":{},"core":{}})
            # Derive twelve-month changes only when every monthly component observation is available.
            for basket,line in [("headline",1),("core",25)]:
                if line not in lines:continue
                y,m=map(int,ym.split("-"));series=[]
                for offset in range(11,-1,-1):
                    serial=y*12+m-1-offset
                    dt=f"{(serial//12):04d}-{(serial%12)+1:02d}"
                    value=byperiod.get(dt,{}).get(line,{}).get("mom")
                    if value is None:series=[];break
                    series.append(value)
                z=dst[basket]
                z["mom"]=lines[line]["mom"]
                z["yoy"]=round(100*(__import__("functools").reduce(lambda a,b:a*(1+b/100),series,1)-1),4) if series else None
                z["items"]=[{"name":v["name"] or ("BEA line "+str(k)),"mom":v["mom"],"yoy":None,"weight":None} for k,v in sorted(lines.items())] if basket=="headline" else []
                z["warning"]="BEA PCE monthly percentage changes; YoY calculated by compounding published rounded monthly rates. Category contribution weights unavailable."
        data["pce"]["note"]="BEA Table 2.8.7 monthly rates; YoY is calculated from rounded monthly changes. PCE contributions unavailable."
        print("PCE refreshed",len(byperiod),"months")
    except Exception as ex:print("PCE refresh unavailable:",ex)
update_cpi()
update_pce()
J.write_text(json.dumps(data,indent=2)+"\n")
