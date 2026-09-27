# PvpBot Wiki

Documentazione di PvpBot: installazione, comandi, selettori, tutte le impostazioni e le funzioni principali. Il sito è
statico e viene servito così com'è da GitHub Pages.

## Struttura

| Percorso | Cosa contiene |
|---|---|
| `content/*.html` | Le pagine della wiki. Si modificano queste. |
| `content/data/settings-schema.json` | Le impostazioni di PvpBot: nome, gruppo, tipo, limiti e valore predefinito. |
| `content/data/settings-it.json` | La descrizione in italiano di ogni impostazione. |
| `assets/` | Stile, script (tema, menu, ricerca) e indice di ricerca generato. |
| `build.py` | Il generatore. |
| `*.html` nella radice | Le pagine generate, pubblicate da GitHub Pages. Non modificarle a mano. |

## Modificare la wiki

1. Modifica o aggiungi una pagina in `content/`. Ogni pagina inizia con un'intestazione:

   ```
   ---
   title: Comandi
   section: Riferimento
   order: 10
   icon: ⌨️
   lead: La frase sotto il titolo.
   ---
   ```

   `section` è una tra `Introduzione`, `Riferimento`, `Funzioni` e `Aiuto`. `order` decide la posizione nella barra
   laterale. Scrivi `{{settings:combat}}` (o un altro gruppo) per inserire la tabella delle impostazioni di quel gruppo.
2. Rigenera il sito (serve solo Python 3, nessuna libreria):

   ```
   python3 build.py
   ```

3. Fai il commit sia di `content/` sia delle pagine generate.

Quando PvpBot aggiunge un'impostazione, aggiungila a `settings-schema.json` e scrivi la sua descrizione in
`settings-it.json`. Se manca la descrizione italiana, viene usata quella inglese dello schema.

## Pubblicazione

In GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch `main`, cartella
`/ (root)`. Il file `.nojekyll` fa servire i file così come sono.
