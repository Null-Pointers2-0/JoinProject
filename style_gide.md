# 🎬 StreamSync Style Guide
> **Cinematic Minimalism · Neon Night · v1.0**

Esta guía define la identidad visual de **StreamSync**: una estética oscura con acentos de cian neón y superficies de cristal (*glassmorphism*).

---

## 🎨 Paleta de Colores

| Color | Nombre | Hex / RGBA | Uso |
| :--- | :--- | :--- | :--- |
| ⚫ | **Deep Black** | `#0B0C10` | Fondo principal de la aplicación. |
| 🧊 | **Glass Surface** | `#1F2833` | Superficie de tarjetas y componentes. |
| ⚡ | **Neon Cyan** | `#66FCF1` | Color de acento, bordes activos y botones. |
| ⚪ | **Text Primary** | `#E0E6ED` | Títulos y texto de alta visibilidad. |
| 🔘 | **Text Muted** | `#8A8D91` | Metadatos, descripciones y hints. |
| ✨ | **Rating Gold** | `#F5C518` | Estrellas de valoración y ratings. |

---

## 🔡 Tipografía

### **Fuentes Principales**
* **Syne (Bold):** Reservada para Logotipos, títulos de secciones y nombres de películas.
* **DM Sans (Medium/Regular/Light):** Utilizada para toda la interfaz de usuario, botones, entradas de texto y párrafos.

### **Escala Tipográfica**
* **Headings:** `Syne Bold · 24px · -0.03em spacing`
* **UI Labels:** `DM Sans Medium · 15px` (Tabs, botones)
* **Body Text:** `DM Sans Regular · 13px` (Contenido general)
* **Metadata:** `DM Sans Light · 12px` (Fechas, emails)
* **Section Labels:** `DM Sans Regular · 10px · Uppercase · 0.10em spacing`

---

## 📐 Espaciado y Bordes

### **Sistema de Espaciado**
| Valor | Nombre | Uso Sugerido |
| :--- | :--- | :--- |
| `4px` | Micro | Separación mínima entre elementos relacionados. |
| `8px` | Small | Gap interno entre elementos de un componente. |
| `12px` | Medium | Gap entre componentes pequeños. |
| `16px` | Large | Padding interno de tarjetas (cards). |
| `24px` | Section | Margen entre secciones principales. |

### **Border Radius**
* **Badges:** `4px`
* **Inputs / Buttons:** `6px`
* **Cards:** `8px`
* **Avatars:** `50%` (Círculo completo)

---

## 💎 Componentes Clave

* **Glass Card:** Fondo `#1F2833` con un borde sutil `rgba(102, 252, 241, 0.08)`. Al hacer *hover*, el borde aumenta su opacidad a `0.22`.
* **Buttons:**
    * *Primary:* Borde cian neón, texto cian, sin fondo sólido.
    * *Ghost:* Borde tenue, texto silenciado.
* **Movie Card:** Diseño minimalista con calificación en oro y género en cian neón.
* **Avatar:** Contenedor circular con brillo neón (*glow*) de `14px` de radio en color cian.

---

## ⚙️ Variables CSS (Custom Properties)

Puedes copiar este bloque directamente en tu archivo global de estilos:

```css
:root {
  /* Colors */
  --bg-deep: #0B0C10;
  --bg-glass: #1F2833;
  --neon-cyan: #66FCF1;
  --neon-glow: rgba(102, 252, 241, 0.15);
  --text-primary: #E0E6ED;
  --text-muted: #8A8D91;
  
  /* Borders */
  --border-glass: rgba(102, 252, 241, 0.08);
  --border-glass-hover: rgba(102, 252, 241, 0.22);
  
  /* Accent */
  --rating-gold: #f5c518;
}