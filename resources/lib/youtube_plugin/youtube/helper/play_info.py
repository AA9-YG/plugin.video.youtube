import math
import requests 

def num_fmt(num):
    i_offset = 15 # change this if you extend the symbols!!!
    prec = 3
    fmt = '.{p}g'.format(p=prec)
    symbols = ['q', 'T', 'B', 'M', 'k', '', 'm', 'u', 'n']

    e = math.log10(abs(num))
    if e >= i_offset + 3:
        return '{:{fmt}}'.format(num, fmt=fmt)
    for i, sym in enumerate(symbols):
        e_thresh = i_offset - 3 * i
        if (num >= 995) and (num < 1000):
            return '1k'
        elif (num >= 999500) and (num < 1000000):
            return '1M'
        elif (num >= 999500000) and (num < 1000000000):
            return '1B'
        elif (num >= 999500000000) and (num < 1000000000000):
            return '1T'
        elif (num >= 999500000000000) and (num < 1000000000000000):
            return '1q' 
        if e >= e_thresh:
            return '{:{fmt}}{sym}'.format(num/10.**e_thresh, fmt=fmt, sym=sym)
    
    return '{:{fmt}}'.format(num, fmt=fmt)
