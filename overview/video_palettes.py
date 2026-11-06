"""Low-saturation video palettes, independent of the studio's interface theme."""
from typing import Literal

VideoPalette=Literal['oceano','papel','noturno','grafite','ardosia','areia','linho','oliva',
    'argila','nevoa','petroleo','taupe','lavanda','cafe','marfim']

# Background, card, text, accent, secondary text. Original three are unchanged.
PALETTES={
    'oceano':('#081f2b','#143b48','#f0faf4','#74f0b2','#a5c6ca'),
    'papel':('#f6f2e9','#e8e3d8','#172c32','#087c69','#506a70'),
    'noturno':('#17172c','#282943','#f7f4ff','#cfb6ff','#b5afcb'),
    'grafite':('#202329','#31353c','#f1f1ed','#b8c7c5','#b0b5ba'),
    'ardosia':('#253039','#35424c','#f4f5f2','#a7bec7','#b1bdc3'),
    'areia':('#eee8dc','#e0d6c5','#302f2b','#6c705c','#65645c'),
    'linho':('#f4f0e6','#e6dfd0','#34332f','#7c6954','#69665e'),
    'oliva':('#2c332c','#3d463b','#f1f1e6','#b8bea0','#bcc2b2'),
    'argila':('#e9ddd4','#d9c7bc','#3f3330','#856153','#72615a'),
    'nevoa':('#e7eceb','#d4dfdd','#273b3b','#526f68','#5a6d69'),
    'petroleo':('#1f3035','#30454b','#eaf0ec','#adc5c2','#adbdba'),
    'taupe':('#e6dfd7','#d7cbc0','#3c3531','#7c6757','#70645b'),
    'lavanda':('#e9e5eb','#d8d1dc','#3c3441','#76647c','#6e6173'),
    'cafe':('#302926','#443a34','#f3ece2','#ceb79d','#c6b8aa'),
    'marfim':('#f8f5ed','#e9e2d5','#35362f','#667255','#707268'),
}
NAMES=['Oceano · verde','Papel · claro','Noturno · violeta','Grafite · cinza escuro',
    'Ardósia · azul acinzentado','Areia · bege suave','Linho · creme neutro','Oliva · verde discreto',
    'Argila · terracota suave','Névoa · cinza esverdeado','Petróleo · azul sóbrio','Taupe · bege acinzentado',
    'Lavanda · violeta suave','Café · marrom escuro','Marfim · branco quente']

def catalog():
    return [{'id':key,'nome':name,'fundo':p[0],'cartao':p[1],'texto':p[2],'destaque':p[3],'secundario':p[4]}
            for (key,p),name in zip(PALETTES.items(),NAMES)]
