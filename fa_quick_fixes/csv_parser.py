import json
pods="PODS_FUSION.json"
csv="fleet_scan_rman_backups.csv"
out_data="data.csv"

with open(csv,'r') as cs:
    cs_data = cs.readlines()
    for line in cs_data:
        pod_name=line.split(',')[1]
        with open(pods,'r') as jd:
            j=json.load(jd)
            for i in j["pods_data"]:
                if i["name"] == pod_name:
                    exadata_list=[]
                    for exa in i["exadatas"]:
                        exadata_list.append(exa["hostname"])
                    exa_str=""
                    for exa in exadata_list:
                        exa_str +="{0}|".format(exa)
                    with open(out_data,'a') as data:
                        d= "{0},{1}\n".format(line.strip(),exa_str)
                        data.write(d)
                   