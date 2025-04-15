import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ---------------- parâmetros comuns ----------------
comprimento    = 8000    # mm (eixo Y)
largura        = 2500    # mm (eixo X)
altura_nominal = 1500    # mm (altura nominal da carga)
desvio_max     = 500     # mm – desvio máximo (somente para baixo)

# ---------------- grade de amostragem ----------------
y_lines   = np.linspace(-comprimento/3, comprimento/3, 3)
x_targets = np.linspace(-largura/2, largura/2, 20)
Xg, Yg    = np.meshgrid(x_targets, y_lines)

# ---------------- superfície da carga ----------------
np.random.seed(42)
Z_load = altura_nominal + np.random.uniform(-desvio_max, 0, size=Xg.shape)
Z_load = np.clip(Z_load, 0, altura_nominal)
Z_floor = np.zeros_like(Z_load)

# Cálculo do volume (m³)
dx = x_targets[1] - x_targets[0]
dy = y_lines[1] - y_lines[0]
volume_m3 = np.sum(Z_load - Z_floor) * dx * dy / 1e9

# ---------------- Função para adicionar as paredes da caçamba ----------------
def add_container(ax):
    """Desenha o piso e as paredes laterais com limite na superfície do minério."""
    # Piso
    ax.plot_surface(Xg, Yg, Z_floor, color='#8d8d8d', alpha=0.25, edgecolor='none')
    
    # Paredes laterais – os polígonos têm o topo na superfície da carga
    ore_color = (0.55, 0.27, 0.07, 0.6)  # marrom-avermelhado com transparência
    polys = []
    
    # Esquerda: x = x_targets[0]
    x_min = x_targets[0]
    for i in range(len(y_lines)-1):
        polys.append([
            (x_min, y_lines[i], 0),
            (x_min, y_lines[i+1], 0),
            (x_min, y_lines[i+1], Z_load[i+1, 0]),
            (x_min, y_lines[i],   Z_load[i,   0])
        ])
    
    # Direita: x = x_targets[-1]
    x_max = x_targets[-1]
    for i in range(len(y_lines)-1):
        polys.append([
            (x_max, y_lines[i], 0),
            (x_max, y_lines[i+1], 0),
            (x_max, y_lines[i+1], Z_load[i+1, -1]),
            (x_max, y_lines[i],   Z_load[i,   -1])
        ])
    
    # Fundo: y = y_lines[0]
    y_min = y_lines[0]
    for j in range(len(x_targets)-1):
        polys.append([
            (x_targets[j],   y_min, 0),
            (x_targets[j+1], y_min, 0),
            (x_targets[j+1], y_min, Z_load[0, j+1]),
            (x_targets[j],   y_min, Z_load[0, j])
        ])
    
    # Frente: y = y_lines[-1]
    y_max = y_lines[-1]
    for j in range(len(x_targets)-1):
        polys.append([
            (x_targets[j],   y_max, 0),
            (x_targets[j+1], y_max, 0),
            (x_targets[j+1], y_max, Z_load[-1, j+1]),
            (x_targets[j],   y_max, Z_load[-1, j])
        ])
    
    polycoll = Poly3DCollection(polys, facecolors=ore_color, edgecolors='none')
    ax.add_collection3d(polycoll)

# ---------------- Função para gerar os raios do LIDAR ----------------
def gerar_rays(full=False):
    """
    Gera raios para 3 linhas de varredura (usando y_lines e x_targets).
    Se 'full' for True, o ponto final do raio será a superfície da carga (de Z_load);
    caso contrário, o raio atinge o piso (Z = 0).
    """
    # Posição fixa do LIDAR
    x_lidar = 0
    y_lidar = -(comprimento/2 + 1000)  # 1 m atrás
    z_lidar = altura_nominal + 1000    # 1 m acima da borda
    rays = []
    
    for i in range(len(y_lines)):
        for j in range(len(x_targets)):
            if full:
                z_t = Z_load[i, j]
            else:
                z_t = 0
            start = np.array([x_lidar, y_lidar, z_lidar])
            end   = np.array([x_targets[j], y_lines[i], z_t])
            rays.append((start, end))
    return rays, x_lidar, y_lidar, z_lidar

# Geração dos raios (com seed já definida)
rays_empty, x_lidar, y_lidar, z_lidar = gerar_rays(full=False)
rays_full,  _,       _,       _         = gerar_rays(full=True)

# ======================== GRÁFICO 1 – Raios do LIDAR (3D) ========================
fig1 = plt.figure(figsize=(10, 7))
ax1 = fig1.add_subplot(111, projection='3d')

# Adiciona o container (piso + paredes)
add_container(ax1)

# Desenha os raios do LIDAR:
# - Linhas sólidas para o "vazio" (atinge o piso)
for s, e in rays_empty:
    ax1.plot([s[0], e[0]], [s[1], e[1]], [s[2], e[2]],
             color='blue', linestyle='solid', linewidth=0.8, alpha=0.7)

# - Linhas tracejadas para a carga (atinge a superfície real)
for s, e in rays_full:
    ax1.plot([s[0], e[0]], [s[1], e[1]], [s[2], e[2]],
             color='red', linestyle='dashed', linewidth=0.8, alpha=0.8)

# Marca a posição do LIDAR
ax1.scatter([x_lidar], [y_lidar], [z_lidar], color='k', marker='o', s=50, label='Lidar')

# Configura os eixos – usando a mesma escala do gráfico 2 (z até altura_nominal)
ax1.set_title("Raios 3‑D do LIDAR com Caçamba")
ax1.set_xlabel("X – Largura (mm)")
ax1.set_ylabel("Y – Comprimento (mm)")
ax1.set_zlabel("Z – Altura (mm)")
ax1.set_xlim(-largura/2, largura/2)
ax1.set_ylim(-comprimento/2, comprimento/2)
ax1.set_zlim(0, altura_nominal)
ax1.view_init(elev=25, azim=-60)
ax1.legend()
plt.tight_layout()

# ======================== GRÁFICO 2 – Superfície da Carga (3D) ========================
fig2 = plt.figure(figsize=(10, 7))
ax2 = fig2.add_subplot(111, projection='3d')

# Adiciona o container (piso + paredes)
add_container(ax2)

# Superfície da carga com colormap "copper"
surf = ax2.plot_surface(Xg, Yg, Z_load,
                        cmap='copper',
                        edgecolor='k',
                        linewidth=0.2,
                        alpha=0.95)

# Atualiza o volume (m³)
volume_m3 = np.sum(Z_load - Z_floor) * dx * dy / 1e9

# Configuração dos eixos e título com volume
ax2.set_title(f"Superfície da Carga – Volume ≈ {volume_m3:.1f} m³")
ax2.set_xlabel("X – Largura (mm)")
ax2.set_ylabel("Y – Comprimento (mm)")
ax2.set_zlabel("Z – Altura (mm)")
ax2.set_xlim(-largura/2, largura/2)
ax2.set_ylim(-comprimento/2, comprimento/2)
ax2.set_zlim(0, altura_nominal)
fig2.colorbar(surf, shrink=0.5, label='Altura (mm)')
ax2.view_init(elev=25, azim=-60)
plt.tight_layout()

# ======================== GRÁFICOS 2D DOS PERFIS COM PROJEÇÃO DOS RAIOS ========================
# Para cada linha de varredura (valor fixo de y em y_lines), gera o perfil 2D e projeta os raios do LIDAR que atingem a superfície.
for i in range(len(y_lines)):
    fig, ax = plt.subplots(figsize=(8, 4))
    # Plot do perfil da carga para o y fixo (valor de Z_load em função de x_targets)
    ax.plot(x_targets, Z_load[i, :], marker='o', linestyle='-', color='green', label='Perfil de Carga')
    
    # Plota os raios do LIDAR sobre o perfil:
    # Para cada x_target correspondente nesta linha de varredura, traça uma reta do LIDAR até o ponto na superfície.
    for j, x_val in enumerate(x_targets):
        ax.plot([x_lidar, x_val], [z_lidar, Z_load[i, j]], 
                linestyle='dashed', linewidth=0.8, color='red', alpha=0.8)
    
    # Marca a posição do LIDAR (projetada no gráfico 2D: usa x e z)
    ax.scatter(x_lidar, z_lidar, color='k', marker='o', s=50, label='Lidar')
    
    ax.set_title(f"Perfil 2D da Carga para y = {y_lines[i]:.1f} mm")
    ax.set_xlabel("X – Largura (mm)")
    ax.set_ylabel("Z – Altura (mm)")
    # Ajusta o limite do eixo Z para incluir o LIDAR (z_lidar = altura_nominal + 1000)
    ax.set_ylim(0, z_lidar + 500)
    ax.grid(True)
    ax.legend()
    plt.tight_layout()

plt.show()
