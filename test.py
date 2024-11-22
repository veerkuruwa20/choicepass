import pickle
f=open('creds.dat','rb')
while True:
    try:
        print(pickle.load(f))
    except:
        f.close()
        break