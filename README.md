# JoinProject

Aquest projecte és una aplicació web feta amb **Django** tracta de fer una web centralitzant les plataformes de streaming per a que els usuaris puguin mirar diferents continguts sense haver de canviar de plataforma.

## Com engegar el projecte amb Docker

El projecte està totalment containeritzat. Només necessites tenir **Docker** i **Docker Compose** instal·lats a la teva màquina.

### 1. Preparació inicial
Clona el repositori i crea el fitxer de variables d'entorn:
```bash
git clone <URL_DEL_TEU_REPOSITORI>
cd <NOM_DEL_PROJECTE>

# Crea el fitxer .env
gedit .env
# O copial del teu ja existent 
cp /el_teu_direcori/.env .env
```
### 2. Iniciar la web
```bash
docker compose up
```
aquesta web estara corrent en **127.0.0.1:8000**