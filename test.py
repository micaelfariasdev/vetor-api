import xml.etree.ElementTree as ET
print("Lendo o arquivo XML...")
tree = ET.parse('sky2.xml')
root = tree.getroot()
print(root)

ns = {'p': 'http://schemas.microsoft.com/project'}

for task in root.findall('p:Tasks/p:Task', ns):
    nome = task.find('p:Name', ns)
    inicio = task.find('p:Start', ns)
    fim = task.find('p:Finish', ns)
    nivel = task.find('p:OutlineLevel', ns)
    intnivel = int(nivel.text)
    if intnivel == 0:
        continue
    print(
        '-' * int(nivel.text),
        'Tarefa:', nome.text if nome is not None else '',
        'Início:', inicio.text if inicio is not None else '',
        'Fim:', fim.text if fim is not None else ''
    )