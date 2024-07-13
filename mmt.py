import math
import parse
import subprocess

## Set once and for all the mean-tone factor for equal temperament
ET = math.log(2**(7/12)*2/3)/math.log(80/81)

class Sound():
    def __init__(self, cscode: str, tempo: int=120):
        self.csfile = "t 0 " + str(tempo) + "\n" + cscode + "e"

    @property
    def play(self):
        print("We play the following code in CSound:\n")
        print(self.csfile + "\n")
        subprocess.run("echo \"" + self.csfile + "\" | csound -o dac orch.orc /dev/stdin",
                       shell = True,
                       capture_output = True,
                       executable="/bin/bash")
        
class Pair:
    def __init__(self, y: int, z: int=0):
        self.y = y  # the fifth        (2:3)
        self.z = z  # the ‘pure’ third (4:5)
        self.v = [self.y,self.z]
        
    def __eq__(self, other):
        return (self.v == other.v and type(self) == type(other))

    def __lt__(self, other):
        return (self.y < other.y or (self.y == other.y and self.z < other.z))
    
class Triple(Pair):
    def __init__(self, x: int, y: int, z: int=0):
        super().__init__(y,z)
        self.x = x  # the octave       (1:2)
        self.v = [self.x,self.y,self.z]

class Interval(Triple):
    def __radd__(self, other):
        return Interval(*[a+b for a,b in zip(self.v,other.v)])

    def __sub__(self, other):
        return Interval(*[a-b for a,b in zip(self.v,other.v)])

    def __rmul__(self, k: int):
        return Interval(*[k*a for a in self.v])

    def __neg__(self):
        return Interval(*[-a for a in self.v])

    def ratio(self,mean: float=0) -> float:
        # whenever float is non-zero, it does not make
        # much sense to have z to be non-zero as well.
        return round((2**self.x)*(((3/2)*(80/81)**mean)**self.y)*((5/4)**self.z),4)

    @property
    def steps(self) -> int:
        return 7*self.x + 4*self.y + 2*self.z

    @property
    def semitones(self) -> int:
        return 12*self.x + 7*self.y + 4*self.z

    @property
    def spn(self) -> str:
        return str(1+abs(self.steps))

class Base(int):
    def __eq__(self,other):
        return (self%7 == other%7)
    
    def __radd__(self, other: int):
        return Base((self+other)%7)

    def __repr__(self):
        return chr(65+(self%7))

class Alter(int):
    def __repr__(self):
        return parse.signed_char(self,"#","b")

class Comma(int):
    def __repr__(self):
        return parse.signed_char(self,"P","M")

class PitchClass(Pair):
    @classmethod
    def spn(cls, spn: str):
        base   = ord(spn[0])-65
        alter  = spn.count("#") - spn.count("b")
        comma  = spn.count("P") - spn.count("M")
        
        Y = [0,2,-3,-1,1,-4,-2]
            
        return cls(Y[base]+7*alter+4*comma,-comma)

    @property
    def base(self) -> Base:
        return Base(4*(self.y+4*self.z))

    @property
    def alter(self) -> Alter:
        return Alter(math.floor(1/7*(4+self.y+4*self.z)))

    @property
    def comma(self) -> Comma:
        return Comma(-self.z)
    
    def __radd__(self, i: Interval):
        return PitchClass(i.y+self.y,i.z+self.z)

    def __repr__(self) -> str:
        return str(self.base) + str(self.alter) + str(self.comma)

    def __hash__(self):
        return hash(tuple(self.v))

    def __sub__(self, other):
        return Interval(0,self.y-other.y,self.z-other.z)

    
class Pitch(Triple,PitchClass):
    @property
    def octave(self) -> int:
        return 3+self.x-2*self.z+math.floor(4/7*(self.y+4*self.z+3))
        
    @classmethod
    def spn(cls, spn: str):
        octave = int(spn.translate(str.maketrans('','',spn[0]+"#bMP")))
        
        c = PitchClass.spn(spn)     
        x = [0,-1,1,0,-1,2,1]
        
        return cls(-4+octave-4*c.alter-2*c.comma+x[c.base%7],c.y,c.z)
           
    def __radd__(self, first: Interval):
        return Pitch(*[a+b for a,b in zip(first.v,self.v)])

    def __sub__(self, other):
        return Interval(*[a-b for a,b in zip(self.v,other.v)])

    @property
    def chroma(self) -> int:
        return Interval(*self.v).semitones

    def freq(self,mean: float=0,cp: float=440) -> float:
        return round(cp*(self - Pitch(0,0,0)).ratio(mean),4)

    def __repr__(self) -> str:
        return str(self.base) + str(self.octave) + str(self.alter) + str(self.comma)

    def __hash__(self):
        return hash(tuple(self.v))

    def pclass(self) -> PitchClass:
        return PitchClass(self.y,self.z)

    def cscode(self,vol: int=100,length: int=1,mean: float=0,cp: float=440) -> str:
        return "i1 0 " + str(length) + " " + str(vol) + " " + str(self.freq(mean,cp))

class ClassChord():
    def __init__(self, *args: PitchClass):
        self.S = {k for k in args}

    def __eq__(self, other):
        return self.S == other.S

    def __radd__(self, i: Interval):
        return self.__class__(*[i+k for k in self.S])

    def mirror(self, a: PitchClass):
        return self.__class__(*[2*(a-k)+k for k in self.S])
    
    def __repr__(self):
        return str(self.S)

    def __mul__(self, other):
        return Chord(*[k for k in set.intersection(self.S,other.S)])
    
class Chord(ClassChord):
    def __init__(self, *args: Pitch):
        self.S = {k for k in args}

    @property
    def classc(self):
        return ClassChord(*[k.pclass for k in self.S])

    def cscode(self,mean: float=0,cp: float=440) -> str:
        vol = round(90/len(self.S),0) # avoid that the waves sum up to an amplitude >100
        cscode = ""
        for p in self.S: cscode += p.cscode(vol,6,mean,cp) + "\n"
        return cscode

    def sound(self,*args) -> Sound:
        return Sound(self.cscode(*args))

class Genus(int):
    def __eq__(self,other):
        return (self%2 == other%2)

    def __repr__(self):
        match self%2:
            case 0: return "major"
            case 1: return "minor"

class Triad(ClassChord):
    def __init__(self, *args: PitchClass):
        super().__init__(*args)
                
        if Interval(0,1,0)+min(self.S) in self.S:
            self.root  = min(self.S)
            self.genus = Genus(0)
        else:
            self.root  = Interval(0,-1,0)+max(self.S)
            self.genus = Genus(1)
            
    @property
    def fifth(self):
        return Interval(0,1,0)+self.root

    @property
    def third(self):
        return min(self.S - {self.root, self.fifth})
    
    @property
    def var(self):
        return Interval(0,1,0)+self.mirror(self.root)

    def par_gar(self,w: int):
        X = [self.root,self.fifth]
        return (self.third-X[(w+self.genus)%2]) + self.mirror(X[(w+self.genus)%2])

    @property
    def par(self):
        return self.par_gar(0)

    @property
    def gar(self):
        return self.par_gar(1)

    def __repr__(self):
        return str(self.root) + " " + str(self.genus) + ": " + str(self.S)
