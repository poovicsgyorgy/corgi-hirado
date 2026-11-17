import requests, json, time
for url,body in [("https://text.pollinations.ai/openai",{"model":"openai","messages":[{"role":"user","content":"Írj egy rövid kitalált corgis hírcímet magyarul. Csak JSON: {\"title\":\"...\"}"}]}),
                 ("https://text.pollinations.ai/openai",{"model":"mistral","messages":[{"role":"user","content":"Írj egy rövid kitalált corgis hírcímet magyarul. Csak JSON: {\"title\":\"...\"}"}]})]:
    t=time.time()
    try:
        r=requests.post(url,json=body,timeout=90); print("==",body["model"],r.status_code,r.headers.get("content-type"),round(time.time()-t,1),repr(r.text[:400]))
    except Exception as e: print("==",url,"HIBA",e)
try:
    r=requests.get("https://text.pollinations.ai/"+requests.utils.quote("Írj egy kitalált corgis hírcímet magyarul."),timeout=90); print("== GET",r.status_code,repr(r.text[:300]))
except Exception as e: print("== GET HIBA",e)
