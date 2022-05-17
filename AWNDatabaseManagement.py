#!/pkg/ldc/bin/python3
#-----------------------------------------------------------------------------
# Name:        AWNDatabaseManagement.py
# Purpose:
#
# Author:      Horacio
#
# Created:     2008/06/10
# Load AWN database and provide some simple access functions
#-----------------------------------------------------------------------------

import xml.parsers.expat
import re
from string import *
import sys

class ITEM:
    "item tuple"
    def __init__(self,itemid,offset,name,type,pos):
        self.__init_vars(itemid,offset,name,type,pos)
    def __init_vars(self,itemid,offset,name,type,pos):
        self._content=[offset,name,type,pos]
        self._itemid=itemid
        self._links_out=[]
        self._links_in=[]
    def get_itemid(self):
        return self._itemid
    def get_offset(self):
        return self._content[0]
    def get_name(self):
        return self._content[1]
    def get_type(self):
        return self._content[2]
    def get_pos(self):
        return self._content[3]
    def put_link(self,itemid1,itemid2,type):
        if self._itemid == itemid1:
            self._links_out.append([type,itemid2])
        elif self._itemid == itemid2:
            self._links_in.append([type,itemid1])
##get_links:
##    input:
##        direcc: direction of the link
##            'in' or 'out'
##        type: type of the link (e.g. 'has_hyponym')
##            default 'all'
##    output:
##        list of tuples:
##            each tuple contains:
##                type of link
##                the other item of the link
    def get_links(self,direcc,type='all'):
        if direcc == 'in':
            return filter(lambda x:(x[0]==type) or (type=='all'),self._links_in)
        else:
            return filter(lambda x:(x[0]==type) or (type=='all'),self._links_out)
    def describe(self):
        print ('itemid ', self._itemid)
        print ('offset ', self._content[0])
        print ('name ', self._content[1])
        print ('type ', self._content[2])
        print ('pos ', self._content[3])
        print ('input links ',self._links_in)
        print ('output links ',self._links_out)

class WORD:
    "word tuple"
    def __init__(self,wordid,value,synsetid):
        self.__init_vars(wordid,value,synsetid)
    def __init_vars(self,wordid,value,synsetid):
        self._value=value
        self._wordid=wordid
        self._synsets=[synsetid]
        self._forms=[]
    def get_roots(self):
        return filter(lambda x:(x[0]=='root'),self._forms)
    def get_forms(self,type='all'):
        return filter(lambda x:(x[0]==type) or (type=='all'),self._forms)
    def put_form(self,form,type):
        self._forms.append((type,form))
    def put_synset(self,synsetid):
        self._forms.append(synsetid)
    def describe(self):
        print ('wordid ', self._wordid)
        print ('value ', self._value)
        print ('synsets ', self._synsets)
        print ('forms ', self._forms)

class FORM:
    "form tuple"
    def __init__(self,form,wordid,type):
        self.__init_vars(form,wordid,type)
    def __init_vars(self,form,wordid,type):
        self._form=form
        self._words=[(type,wordid)]
    def put_word(self,wordid,type):
        self._words.append((type,wordid))
    def get_words(self,type='all'):
        return filter(lambda x:(x[0]==type) or (type=='all'),self._words)
    def describe(self):
        print ('form ', self._form)
        print ('words ', self._words)

        

class WN:
    "representation of a WN"
    def __init__(self):
        self.__init_vars()
    
    def __init_vars(self):
        self._source_counts = {
            'item':0,
            'link':0,
            'word':0,
            'form':0,
            'verbFrame':0,
            'authorship':0,
            'all':0}
        self._items = {}
        self._words = {}
        self._forms = {}
        self._index_w = {}
        self._index_f = {}

##summary:
##    short description of the content of WN

    def summary(self):
        for i in self._source_counts.keys():
            print (i+'\t'+str(self._source_counts[i]))
  
    def update_item(self,itemid,offset,name,type,pos):
        if itemid in self._items:
            print ('itemid '+itemid+' duplicated, ignored')
        else:
            self._items[itemid]=ITEM(itemid,offset,name,type,pos)
        
    def update_link(self,itemid1,itemid2,type):
        if not itemid1 in self._items:
            print ('itemid1 '+itemid1+' not present, ignored')
        elif not itemid2 in self._items:
            print ('itemid2 '+itemid2+' not present, ignored')
        else:
            self._items[itemid1].put_link(itemid1,itemid2,type)
            self._items[itemid2].put_link(itemid1,itemid2,type)

    def update_word(self, wordid, value, synsetid):
        if not synsetid in self._items:
           print ('synsetid '+synsetid+' not present, ignored')
        else:
            if wordid  in self._words:
                self._words[wordid].put_synset(synsetid)
            else:
                self._words[wordid] =WORD(wordid, value, synsetid)
            
    def update_form(self, value, wordid, type):
        if not wordid in self._words:
           print ('wordid '+wordid+' not present, ignored')
        else:
            self._words[wordid].put_form(value, type)
            if value in self._forms:
                self._forms[value].put_word(wordid, type)
            else:
                self._forms[value]=FORM(value,wordid, type)

    def compute_index_w(self):
        for i in self._words.keys():
            w=self._words[i]
            if w._value in self._index_w:
                self._index_w[w._value].append(w._wordid)
            else:
                self._index_w[w._value]=[w._wordid]

    def compute_index_f(self):
        for i in self._forms.keys():
            f=self._forms[i]
            if f._form  in self._index_f:
                self._index_f[f._form].append(f.get_words())
            else:
                self._index_f[f._form]=f.get_words()

    def count_words(self):
        return len(self._words.keys())
    
    def count_forms(self):
        return len(self._forms.keys())

    def count_synsets(self):
        return len(filter(lambda x:self._items[x].get_type()=='synset',self._items.keys()))

##get_words:
##    input:
##        simple: True or False
##    output:
##        if simple:
##            list of words
##        else:
##            list of pairs <word, wordid>
            
    def get_words(self,simple=False):
        if simple:
            return self._index_w.keys()
        else:
            l=[]
            for i in self._index_w.keys():
                l.append((i,self._index_w[i]))
            return l

##get_forms:
##    input:
##        simple: True or False
##    output:
##        if simple:
##            list of forms
##        else:
##            list of pairs <form, list of pairs <type, wordid>>
    
    def get_forms(self,simple=False):
        if simple:
            return self._index_f.keys()
        else:
            l=[]
            for i in self._index_f.keys():
                l.append((i,self._index_f[i]))
            return l

##get_wordids_from_word:
##    input: a word
##    output: list of wordid

    def get_wordids_from_word(self,word):
        if word in self._index_w:
            return self._index_w[word]
        else:
            return None

##get_forms_from_word:
##    input: a word
##    output: list of forms

    def get_forms_from_word(self,word):
        wis=self.get_wordids_from_word(word)
        if wis:
            forms=set()
            for i in wis:
                f=self._words[i].get_forms()
                if f:
                    forms.update(f)
            return list(forms)
        else:
            return None

##get_roots_from_word:
##    input: a word
##    output: list of roots

    def get_roots_from_word(self,word):
        wis=self.get_wordids_from_word(word)
        if wis:
            forms=set()
            for i in wis:
                f=self._words[i].get_roots()
                if f:
                    forms.update(f)
            return map(lambda x:x[1],list(forms))
        else:
            return None

##get_synsetids_from_word:
##    input: a word
##    output: list of synsetids

    def get_synsetids_from_word(self,word):
        wis=self.get_wordids_from_word(word)
        if wis:
            synsets=set()
            for i in wis:
                synset=self._words[i]._synsets
                if synset:
                    synsets.update(synset)
            return list(synset)
        else:
            return None

##get_synsets_from_word:
##    input: a word
##    output: list of synsets


    def get_synsets_from_word(self,word):
        sids=self.get_synsetids_from_word(word)
        if sids:
            return map(lambda x:(self._items[x].get_pos(),self._items[x].get_offset()),sids)
        else:
            return None

    def get_form(self,form):
        if form in self._index_f:
            return self._index_f[form]
        else:
            return None
    

    def count_forms(self):
        return len(self._forms.keys())

    def count_synsets(self):
        return len(filter(lambda x:self._items[x].get_type()=='synset',self._items.keys()))


def processCmdlineOpts(cmdOpts):
    """ Process command line options; return a hash that can be passed
    to the application. """
    opts = {}
    for i in range(1,len(cmdOpts)):
        if re.match('-i', cmdOpts[i]):
            opts['i'] = cmdOpts[i+1]
    if not 'i' in opts:
        opts['i']='awn.xml'
    return opts


def start_element(name, attrs):
    global wn
    wn._source_counts['all']+=1
    for i in wn._source_counts.keys():
        if name == i:
            wn._source_counts[i]+=1
            break
    if name == 'item':
        wn.update_item(
            attrs['itemid'],
            attrs['offset'],
            attrs['name'],
            attrs['type'],
            attrs['POS'])
    elif name == 'link':
        wn.update_link(
            attrs['link1'],
            attrs['link2'],
            attrs['type'])
    elif name == 'word':
        wn.update_word(
            attrs['wordid'],
            attrs['value'],
            attrs['synsetid'])
    elif name == 'form':
        wn.update_form(
            attrs['value'],
            attrs['wordid'],
            attrs['type'])
    

def end_element(name):
    pass

def char_data(data):
    pass

def _encode(data):
    return data.encode('utf8')


def loadAWNfile(ent):
    global wn
    print ('processing file ', ent)
    try:
        ent = open(ent,mode="rb")
        print (ent)
        wn=WN()
        p.ParseFile(ent)
    except IOError:
        print ('file ',ent,' not correct')

        
def test():
    "tests some functions"
    a=wn.get_words(True)
    print ( 'length of a: ', len(a))
    print ('a[0]: ', a[0])
    b=wn.get_forms(False)
    print ( 'length of b: ', len(a))
    print ('b[0]: ', b[0][0])
    for i in b[0][1]:
        print ('\t',i[0],i[1])
    c=wn._items.keys()
    print  ('length of c: ', len(c))
    print ('c[0]: ', c[0])
    wn._items[c[0]].describe()
    d=wn._words.keys()
    print  ('length of d: ', len(d))
    print ('d[0]: ', d[0])
    wn._words[d[0]].describe()


opts = processCmdlineOpts(sys.argv)
p = xml.parsers.expat.ParserCreate()
p.StartElementHandler = start_element
p.EndElementHandler = end_element
p.CharacterDataHandler = char_data
loadAWNfile(opts['i'])
wn.compute_index_w()
wn.compute_index_f()


