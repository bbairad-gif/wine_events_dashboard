def aggiungi(a, b): return a+b
def sottrai(a, b): return a-b
def moltiplica(a, b): return a*b 
def dividi(a, b): return a/b 
def esce(a,b): return  

print("Indica l'operazione da eseguire: ") 
print ("   1 per addizione") 
print ("   2 per sottrazione") 
print ("   3 per moltiplicazione") 
print ("   4 per divisione") 
print ("   X per uscire") 
scelta = input("Inserisci l'operazione da eseguire: ") 
if scelta != 'X': 
    v1 = float(input("Inserisci il primo numero: ")) 
    v2 = float(input("Inserisci il secondo numero: ")) 
if   scelta=='1': print(v1,"+",v2,"= ",aggiungi(v1,v2)) 
elif scelta=='2': print(v1,"-",v2,"= ",sottrai(v1,v2)) 
elif scelta=='3': print(v1,"x",v2,"= ",moltiplica(v1,v2)) 
elif scelta=='4': 
     if v2==0: print("Divisione per zero non valida") 
     else: print(v1,":",v2,"= ",dividi(v1,v2)) 
elif scelta=='X': print("Il programma esce",esce(0,0))
else: print("Selezione non valida")