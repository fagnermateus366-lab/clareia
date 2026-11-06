"""Closed vocabulary: model output selects recipes, never executable code."""
from typing import Literal

ShotRecipe = Literal['auto','titulo_marcado','palavras_encadeadas','digitacao','titulo_foco',
    'pilha_cartoes','lista_progressiva','rede_conexoes','traco_progressivo',
    'camadas_profundidade','camera_suave','comparacao_revelada','linha_tempo',
    'grade_paineis','foco_luz','destaque_icone','conclusao_limpa',
    'baralho_distribuido','carrossel_horizontal','carrossel_vertical','grade_mosaico',
    'vidro_flutuante','paineis_desfocados','vidro_vitrine','navegador_zoom','janelas_cascata','codigo_foco',
    'faixa_titulo','contorno_preenchido','cascata_diagrama','conectores_etapas','mapa_mental',
    'zoom_impacto','ritmo_acelerado','grade_impacto','monitor_crt','selo_carimbado',
    'volume_piramide','volume_piramide_expandida','volume_funil','volume_colunas','volume_blocos','volume_radial',
    'volume_personagem','volume_fluido','volume_produto','volume_particulas','volume_texto','volume_dispersao',
    'volume_alt_titulo_marcado','volume_alt_palavras_encadeadas','volume_alt_digitacao','volume_alt_titulo_foco','volume_alt_pilha_cartoes','volume_alt_lista_progressiva','volume_alt_rede_conexoes','volume_alt_traco_progressivo','volume_alt_camadas_profundidade','volume_alt_camera_suave','volume_alt_comparacao_revelada','volume_alt_linha_tempo','volume_alt_grade_paineis','volume_alt_foco_luz','volume_alt_destaque_icone','volume_alt_conclusao_limpa','volume_alt_baralho_distribuido','volume_alt_carrossel_horizontal','volume_alt_carrossel_vertical','volume_alt_grade_mosaico','volume_alt_vidro_flutuante','volume_alt_paineis_desfocados','volume_alt_vidro_vitrine','volume_alt_navegador_zoom','volume_alt_janelas_cascata','volume_alt_codigo_foco','volume_alt_faixa_titulo','volume_alt_contorno_preenchido','volume_alt_cascata_diagrama','volume_alt_conectores_etapas','volume_alt_mapa_mental','volume_alt_zoom_impacto','volume_alt_ritmo_acelerado','volume_alt_grade_impacto','volume_alt_monitor_crt','volume_alt_selo_carimbado']
ShotArt = Literal['editorial','cinema','tecnologia','vibrante']
ShotEnergy = Literal['suave','equilibrada','energica']
ShotFinish = Literal['vidro_avancado','original']
ShotFigureSelection = Literal['tematico','rigoroso']
ShotFamily = Literal['auto','tipografia','espacial','editorial','luminoso',
    'cartoes','vidro','interface','diagramas','impacto','retro','volumetrico']

SHOT_FIELDS=('shotcraft_estilo','shotcraft_acabamento','shotcraft_receita','shotcraft_intensidade','shotcraft_orientacao','shotcraft_ia','shotcraft_modelo','shotcraft_selecao_figuras')
