import csv
f=open('requests.csv','w')
csvw=csv.writer(f)
l=['Name','Admission Number','Class','Division','Purpose','Transport','Time']
csvw.writerow(l)

f.close()

f1=open('data.csv','w')
cswr=csv.writer(f1)
d=['Name','Class','Admission Number','Class Teacher','Status','OTP','Time']
cswr.writerow(d)

f1.close()