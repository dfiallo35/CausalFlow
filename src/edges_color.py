import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx


        
def color_edges_standard_deviation(edges:list, min, max):
    """Set color to edges """    
    if(min < 0):
        max=max-min
        edges=[x-min for x in edges]
        min=0        
    range=max-min 
    sd=np.std(edges) 
    med=np.median(edges)
    colors = [] 
    for edge in edges:
        color=int(abs(edge-med)/sd *200)+25
        print(color)
        colors.append(_to_hexa_rgb(color))
    return colors

       
def _to_hexa_rgb(n: int):
    '''
    Convert a number to a hexa color
    :param number: Number to convert
    :type number: int
    :return: Hexa color
    :rtype: str
    '''
    n= str(hex(n))[2:]
    return '#' + 'ff' + n + n

def color_edges(edges:list, min, max):
    """Set color to edges """    
    if(min < 0):
        max=max-min
        pos_edges=[x-min for x in edges]
        min=0        
    range=max-min 
    colors = []
    for edge in pos_edges:
        color=int(abs(edge-min)/range *200)+25
        print(color)
        colors.append(_to_hexa_rgb(color))
    return colors


def to_hexa_rgb(n: int, min, max):
    '''
    Convert a number to a hexa color
    :param number: Number to convert
    :type number: int
    :return: Hexa color
    :rtype: str
    '''
    if(min < 0):
        max=max-min
        n=n-min
        min=0        
    range=max-min 
    colors = []
    color=int(abs(n-min)/range *200)+25
    colors.append(_to_hexa_rgb(color))
    return colors



a=[0.02341, 0.0452, 0.0433, -0.14, 0.238915, 0.0433, -0.18794, 0.2315, 0.08433, 0.13244,-0.2315,1]
colors=color_edges(a, min(a), max(a))
print(colors)
c2=[to_hexa_rgb(n, min(a), max(a)) for n in a]
# print(colors)
print(c2)
print()
c3=color_edges_standard_deviation(a,min(a),max(a))
print(c3)
# colors=[colors[x] for x in colors]
# print(colors)

# hist = cv2.calcHist([c2], [0], None, [256], [0, 256])
# cv2.calcHist(a ,[0], None, [256], [0, 256])




