import subprocess
import threading


def runCommandThreaded(stress_cmd):
    proc = subprocess.run(stress_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) #universal_newlines=True)
    print(proc.stdout.decode())


################
## Main entry
################

# Command to execute (e.g. execute a sqlite3 command in each pod via kubectl exec, dont use -it on exec - it messes up terminal)
stress_cmd_template = '''
time -p kubectl exec -n guest {pod_name} -- \
        sqlite3 /scratch-shared/chembl_23_sqlite/chembl_23.db "SELECT td.PREF_NAME, COUNT(a.STANDARD_VALUE)
                                                                  FROM TARGET_DICTIONARY td, ASSAYS ass, ACTIVITIES a
                                                                  WHERE a.STANDARD_VALUE < 10000 AND
                                                                  a.STANDARD_UNITS = 'nM' AND
                                                                        a.STANDARD_TYPE = 'Ki' AND
                                                                        a.ASSAY_ID = ass.ASSAY_ID AND
                                                                        ass.TID = td.TID AND
                                                                        td.PREF_NAME IS NOT NULL
                                                                  GROUP BY td.PREF_NAME
                                                                  ORDER BY COUNT(a.STANDARD_VALUE) DESC
                                                                  LIMIT 3"
'''

# List/filter pod names where commands will get executed
list_cmd = 'kubectl get po -n guest --no-headers -o custom-columns=":metadata.name" | grep stresstest'
proc = subprocess.run(list_cmd, capture_output=True, shell=True)
pod_names = proc.stdout.decode()

print("pod_names:" + pod_names)

# Execute command for each pod in list of podnames (each in a separate thread)
threads = []
for pod_name in pod_names.split():
    stress_cmd = stress_cmd_template.format(pod_name=pod_name)
    th = threading.Thread(target=runCommandThreaded, args=(stress_cmd,))
    th.start()
    threads.append(th)

# synchronize threads
for t in threads:
    t.join()


print("done")


