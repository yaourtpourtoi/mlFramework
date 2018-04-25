import json

def main():

    C = Cut("-ISO- && -SS-", "et")

    # A = Cut("-MT-")

    # C = C.invert("-ISO-")
    # print C.original
    # C = C+A
    print C.original
    new = C.remove("-ISO-")
    print new.original
    print C.get()

class Cut():

    def __init__(self, cutstring, channel=""):

        self.original = cutstring
        self.channel = channel
        self.cutfile = "conf/cuts.json"

        with open(self.cutfile,"r") as FSO:
            self.cut_alias = json.load(FSO)

        if self.channel:
            self.cut_alias = self.__flatten( self.cut_alias )

        self.InvertD = {
            "-SS-": "-OS-",
            "-OS-": "-SS-",
            "-ISO-": "-ANTIISO-",
            "-ANTIISO-": "-ISO-"
        }

    def __add__(self, new):

        if type(new) == str: return Cut(self.original, self.channel)

        return Cut( " & ".join([self.original, new.original])  , self.channel)

    def __flatten(self,obj):

        for elem in obj:
            obj[elem] = self.__assertChannel(obj[elem])
        return obj


    def __assertChannel(self, obj):

        if type(obj) == dict:   return obj[self.channel]
        else: return obj

    def setChannel(self, channel):
        self.channel = channel
        with open("cuts.json","r") as FSO:
            self.cut_alias = self.__flatten( json.load(FSO) )

    def get(self):
        assert self.channel

        cutstring = self.original
        for alias in self.cut_alias:

            cutstring = cutstring.replace( alias, self.cut_alias[alias])

        return cutstring

    def getForDF(self):

        cutstring = self.get()

        return cutstring.replace("&&","&")

    def switchTo(self,what):

        isos = ["-ISO-","-ANTIISO-","-ANTIISO1-","-ANTIISO2-"]
        cutstring = self.original

        if what in isos:
            for i in isos:

                if cutstring.find(i) != -1:
                    return Cut(cutstring.replace(i, what), self.channel)

    def remove(self, what):
        isos = ["-ISO-","-ANTIISO-","-ANTIISO1-","-ANTIISO2-"]

        parts = self.original.split(" && ")
        cutstring = []

        for p in parts:

            if not what in p: cutstring.append(p)

        cutstring = " && ".join( cutstring )

        return Cut(cutstring, self.channel)

    def invert(self,what):

        cutstring = self.original
        if not type(what) == list:
            what = [what]

        for elem in what:
            if elem in cutstring:
                cutstring = cutstring.replace( elem, self.InvertD[elem]  )

        return Cut(cutstring, self.channel)


    def getInvert(self, what = [] ):
        assert self.channel

        cutstring = self.original
        if not type(what) == list:
            what = [what]

        for elem in what:
            if elem in cutstring:
                cutstring = cutstring.replace( elem, self.InvertD[elem]  )

        for alias in self.cut_alias:

            cutstring = cutstring.replace( alias, self.cut_alias[alias])

        return cutstring


if __name__ == '__main__':
            main()      
