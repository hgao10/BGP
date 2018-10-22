class ASPATH:
  def __init__(self,length_min,length_max):
    self.length = [length_min,length_max]
    self.ASN = [] # Each list element: [ASN,position,frequency]
    #necessary cause ASN member somehow is shared among different objects of ASPATH even though it is declared within the class

class ASPathPart:
  def __init__(self, asn, pos, freq):
    self.asn = asn
    self.pos = pos
    self.freq = freq
  
  def __repr__(self):
    return "ASPathPart<asn: %s, pos: %s, freq: %s>" % (self.asn, self.pos, self.freq)

#An as path with arbitrary length <= 20 is represented by a value of "-1" in the length field. 
aspath = ASPATH(0,21) 

print (aspath.ASN)
print (aspath.length)
if [1,0,0] in aspath.ASN:
  aspath.ASN.remove([1,0,0])

aspathpart1 = ASPathPart(1,0,[0,0])

#aspath.ASN.insert(0, [1,0,0])
#aspath.insert_front(aspathpart1)
aspath.ASN.insert(0,aspathpart1)
if [1,0,[0,0]] in aspath.ASN:
  print("yes, [1,0,[0,0]] is in the list")
  aspath.ASN.remove([1,0,[0,0]])
print (aspath.ASN)

print (len(aspath.ASN))

# Match ^14$ in the aspath, set length to 1 and add [14,0,1] 
aspathpart2 = ASPathPart(14,1,[1,1])
aspath2 = ASPATH(1,1)
aspath2.ASN.insert(0,aspathpart2)
#aspath2.length = [1,1] #length has to be 0
print(aspath2.length, aspath2.ASN)

#generalize ASN number to ^x$
#TODO1

#Match _14_ in the aspath, doesn't care about how many times 14 has appeared or where it is in the as path (-1 represents dont care)
aspath3 = ASPATH(1,20) #length has to be at least 1 and up to 20
aspathpart3 = ASPathPart(14,0,[1,20])
aspath3.ASN.insert(0, aspathpart3)
print(aspath3.length, aspath3.ASN)

#generalize ASN to _x_
#TODO2

#Deny ^14$
aspathpart4 = ASPathPart(-14,1,[1,1])
aspath4 = ASPATH(1,1)
aspath4.ASN.insert(0,aspathpart4)
print(aspath4.length, aspath4.ASN)

#generalize ASN to deny ^x$
#TODO3, 
#return two ASPATH objects, define an ASPATH union class

#deny _14_
aspath5 = ASPATH(1,20)
aspathpart5 = ASPathPart(-14,0,[1,20])
aspath5.ASN.insert(0,aspathpart5)
print(aspath5.length, aspath5.ASN, aspath5.ASN[0].asn)

#if an aspath contains [14, 0,1] then add these two list together, there will be a 0 which
range1 = [1,1]
range2 = [0,2]

def check_subset(list1, list2):
  if(list1[0]>= list2[0] & list1[1]<= list2[1]):
    print("first arg is a subset of the second arg")
    return 1
  else: 
    print("first arg is not a subset of the second arg")
    return 0

check_subset(range1, range2)

def route_decision(aspath_rule, aspath_test):
  match_rule_count = len(aspath_rule.ASN)
  #handles permit clause first:
  if(check_subset(aspath_test.length, aspath_rule.length)== 1):
  #if(aspath_test.length[0]>= aspath_rule.length[0] &aspath_test.length[1]<= aspath_rule.length[1]):
    for x in aspath_rule.ASN :
      if(x.asn >0):
        print(x.asn)
        match_flag = 0
        for y in aspath_test.ASN :
          print(y.asn)
          if(y.asn == x.asn):
            #check if position needs to be matched
            if(x.pos != 0):
              if(x.pos != y.pos):
                print("drop routes due to a mismatch in position in a permit clause %d %d", x.asn, x.pos)
                return
            #check frequencies for a specific ASN
            if(check_subset(y.freq, x.freq) == 1):
              #one match is found
              match_rule_count += -1
              match_flag = 1
              print ("one match found and %d to go", match_rule_count)
            else:
              print("drop route due to a mismatch in frequency in a permit clause %d", x.asn, x.freq)
              return
        if(match_flag == 0):
          print("drop route due to mismatch in asn in a permit clause", x.asn)
          return

      #elif(x.asn <0):
        #start handling deny cases

'''     if(aspath_rule.ASN[0].asn < 0):
      for x in aspath_test.ASN:
        if(x.asn+aspath_rule.ASN[0].asn == 0):
          print("drop route")
          break
    else:
      for x in aspath_test.ASN:
        if(x.asn-aspath_rule.ASN[0].asn == 0):
          if(aspath_rule.ASN[0][1] != 0):
            if(x[0].pos == aspath_rule.ASN[0].pos):
              if(x[0].freq == aspath_rule.ASN[0].freq): #check frequency
                print("match")
                break '''
        
aspath_rule = ASPATH(1,1)
aspath_rule_part = ASPathPart(14, 1, [1,1])
aspath_rule.ASN.insert(0,aspath_rule_part)
aspath_test = ASPATH(1,1)
aspath_test_part = ASPathPart(14, 1, [1,2])
aspath_test.ASN.insert(0,aspath_test_part)  
route_decision(aspath_rule,aspath_test) 



#function to detect if a specific route contains 14 in any location, if there is, drop it 










  




