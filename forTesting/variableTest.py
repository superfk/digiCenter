import re

text = '25+var(Test1)-var(Temp_incre)'

pattern = 'var\((.*?)\)'


variables = {'Test1':100,'Temp_incre':5}


for match in re.findall(pattern, text):
    print(match)
    print(variables[match])

    
