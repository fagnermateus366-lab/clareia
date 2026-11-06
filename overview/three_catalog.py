"""Real WebGL models. These are Clareia components, not upstream 2.5D recipes."""
MODELS=[
 ('volume_piramide','pyramid','Pirâmide em camadas','Uma camada por frase: base, meio e topo. A quarta frase inicia outra pirâmide.','Construção progressiva de até três ideias, mantendo os rótulos anteriores.'),
 ('volume_piramide_expandida','exploded-pyramid','Pirâmide expandida','Constrói base, meio e topo com intervalos entre camadas. Reinicia a cada três frases.','Ideias em sequência, com as camadas anteriores preservadas até completar o conjunto.'),
 ('volume_funil','ring-funnel','Funil de anéis','Anéis com espessura e abertura central em níveis decrescentes.','Etapas de um funil ou seleção progressiva narrada.'),
 ('volume_colunas','columns','Colunas e etapas','Colunas sólidas se formam em sequência.','Etapas qualitativas; não inventar valores nem percentuais.'),
 ('volume_blocos','flow-blocks','Blocos conectados','Sólidos ligados em um fluxo espacial.','Processos com relações explícitas.'),
 ('volume_radial','radial-cubes','Cubos radiais','Quatro cubos coloridos em torno de um centro.','Quatro aspectos paralelos de um assunto.'),
 ('volume_personagem','rigged-viewer','Personagem articulado · GLTF','Modelo GLB local com esqueleto e animações Idle e Walk.','Demonstração de movimento ou personagem ilustrativo; não é retrato real.'),
 ('volume_fluido','metaballs','Líquido volumétrico','Metaballs de geometria real, material físico e shader de superfície.','Metáfora de união, fluidez ou transformação; não simulação científica.'),
 ('volume_produto','product','Produto no pedestal','Gadget tridimensional com material PBR e iluminação de estúdio.','Apresentação ilustrativa de tecnologia; não representa produto real.'),
 ('volume_particulas','galaxy','Galáxia de partículas','Pontos em três dimensões formam braços espaciais.','Contextos cósmicos ou metáforas explicitamente indicadas.'),
 ('volume_texto','text','Texto geométrico','Letras extrudadas com chanfro e reflexos metálicos.','Título ou mensagem curta presente no roteiro.'),
 ('volume_dispersao','scatter','Dispersão em 3D','Eixos X, Y e Z com pontos e materiais volumétricos.','Demonstração ilustrativa identificada como tal; dados reais precisam ser fornecidos.'),
]
RECIPES=[{'id':key,'modelo3d':model,'nome':name,'descricao':description,'usar':use,'origem':'clareia-3d-original',
          'composicoes':['conceito','processo','comparacao','rede']} for key,model,name,description,use in MODELS]
BY_RECIPE={r['id']:r for r in RECIPES}
import json
from pathlib import Path
VARIANTS=json.loads(Path(__file__).with_name('three_variants.json').read_text(encoding='utf-8'))
RECIPES.extend({'id':r['recipe'],'modelo3d':r['id'],'nome':r['name'],'descricao':r['description'],'usar':r['use'],
                'origem':'clareia-3d-original','composicoes':['conceito','processo','comparacao','rede'],
                'acervo3d':r['figures']} for r in VARIANTS)
SUBJECT_IDS={'computador','notebook','celular','castelo','cerebro','livro','arvore','ponte','igreja','robo','microscopio',
             'telescopio','relogio_areia','balanca','camera','microfone','escada','vela','satelite','atomo'}
BY_RECIPE={r['id']:r for r in RECIPES}
