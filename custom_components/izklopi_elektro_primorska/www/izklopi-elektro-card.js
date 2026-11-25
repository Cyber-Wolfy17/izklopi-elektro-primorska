const IZKLOPI_CARD_VERSION = "0.1.0";

class IzklopiElektroCard extends HTMLElement {
  static getConfigForm() {
    return {
      schema: [
        { name: "entity", required: true, selector: { entity: { domain: "sensor" } } },
        { name: "name", selector: { text: {} } },
        { name: "hide_after_end", selector: { boolean: {} } },
      ],
      computeLabel: (s) =>
        ({
          entity: "Entiteta naslednjega izpada",
          name: "Naslov",
          hide_after_end: "Skrij po koncu izpada",
        })[s.name],
    };
  }

  static getStubConfig(hass) {
    const id = Object.keys(hass.states).find(
      (e) => e.startsWith("sensor.") && e.endsWith("naslednji_izpad")
    );
    return { entity: id || "", name: "⚠️ Načrtovan izklop elektrike", hide_after_end: false };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Določi entiteto (entity) senzorja naslednjega izpada.");
    }
    this._config = {
      name: "⚠️ Načrtovan izklop elektrike",
      hide_after_end: false,
      ...config,
    };
    if (!this.shadowRoot) this._build();
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const s = hass.states[this._config?.entity];
    if (s === this._lastState) return;
    this._lastState = s;
    this._render();
  }

  connectedCallback() {
    this._timer = setInterval(() => this._render(), 30000);
    if (this._hass) this._render();
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  getCardSize() {
    return 3;
  }

  _build() {
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        .card {
          background: #1e1e1e;
          color: #fff;
          padding: 16px;
          border-radius: 12px;
          border: 2px solid #ff9800;
          animation: blink-orange 1s step-end infinite;
          display: grid;
          grid-template-columns: 1fr 120px;
          grid-template-rows: min-content 1fr;
          column-gap: 12px;
          row-gap: 14px;
          box-sizing: border-box;
        }
        .card.pre {
          border-color: #ff5252;
          animation-name: blink-red;
        }
        .title {
          grid-column: 1 / -1;
          font-size: 20px;
          font-weight: 600;
          padding-bottom: 4px;
        }
        .info {
          align-self: center;
          line-height: 1.9;
          font-size: 14px;
        }
        .cd {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 4px;
          padding: 8px;
          border-radius: 9px;
          border: 1px solid rgba(255, 152, 0, 0.7);
          background: rgba(255, 152, 0, 0.08);
        }
        .card.pre .cd {
          border-color: rgba(255, 82, 82, 0.7);
          background: rgba(255, 82, 82, 0.08);
        }
        .lbl {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 1px;
          color: #ffcc80;
        }
        .val {
          font-size: 38px;
          font-weight: 800;
          line-height: 1.2;
          color: #ff9800;
        }
        .unit {
          font-size: 12px;
          font-weight: 700;
          color: #ffb74d;
        }
        .card.pre .lbl { color: #ff8a80; }
        .card.pre .val { color: #ff5252; }
        .card.pre .unit { color: #ff9999; }
        @keyframes blink-orange {
          0%, 100% { border-color: #ff9800; }
          50% { border-color: transparent; }
        }
        @keyframes blink-red {
          0%, 100% { border-color: #ff5252; }
          50% { border-color: transparent; }
        }
      </style>
      <div class="card" id="card">
        <div class="title" id="title"></div>
        <div class="info" id="info"></div>
        <div class="cd">
          <div class="lbl" id="lbl"></div>
          <div class="val" id="val"></div>
          <div class="unit" id="unit"></div>
        </div>
      </div>
    `;
    this._els = {
      card: root.getElementById("card"),
      title: root.getElementById("title"),
      info: root.getElementById("info"),
      lbl: root.getElementById("lbl"),
      val: root.getElementById("val"),
      unit: root.getElementById("unit"),
    };
  }

  _render() {
    if (!this._els || !this._config) return;
    const s = this._hass?.states[this._config.entity];
    if (!s || s.state === "unknown" || s.state === "unavailable") {
      this.style.display = "none";
      return;
    }

    const now = Date.now();
    const start = new Date(s.state).getTime();
    const end = new Date(s.attributes.konec).getTime();
    if (isNaN(start) || isNaN(end)) {
      this.style.display = "none";
      return;
    }

    const pre = now < start;
    const during = !pre && now < end;
    if (!pre && !during && this._config.hide_after_end) {
      this.style.display = "none";
      return;
    }
    this.style.display = "";

    const e = this._els;
    e.card.className = "card" + (pre ? " pre" : "");
    e.title.textContent = this._config.name;

    const fmt = (v) => {
      const d = new Date(v);
      if (!v || isNaN(d)) return "—";
      return d
        .toLocaleString("sl-SI", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hourCycle: "h23",
        })
        .replace(",", "");
    };
    const a = s.attributes;
    e.info.innerHTML =
      `<b>Kraj:</b> ${a.kraj || "—"}<br>` +
      `<b>Ulica:</b> ${a.ulica || "—"}<br>` +
      `<b>Od:</b> ${fmt(s.state)}<br>` +
      `<b>Do:</b> ${fmt(a.konec)}`;

    if (!pre && !during) {
      e.lbl.textContent = "IZPAD";
      e.val.textContent = "✓";
      e.unit.textContent = "KONČAN";
      return;
    }

    const target = pre ? start : end;
    const diff = target - now;
    let value, unit;
    if (diff < 3600000) {
      value = Math.ceil(diff / 60000);
      unit = value === 1 ? "MINUTA" : "MINUT";
    } else if (diff < 86400000) {
      value = Math.floor(diff / 3600000);
      unit = value === 1 ? "URA" : "UR";
    } else {
      value = Math.floor(diff / 86400000);
      unit = value === 1 ? "DAN" : "DNI";
    }
    e.lbl.textContent = pre ? "DO IZPADA" : "DO KONCA IZPADA";
    e.val.textContent = value;
    e.unit.textContent = unit;
  }
}

if (!customElements.get("izklopi-elektro-card")) {
  customElements.define("izklopi-elektro-card", IzklopiElektroCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "izklopi-elektro-card")) {
  window.customCards.push({
    type: "izklopi-elektro-card",
    name: "Izklopi Elektro – načrtovan izpad",
    description: "Kartica z odštevanjem do naslednjega načrtovanega izklopa elektrike.",
    preview: false,
  });
}

console.info(`%c IZKLOPI-ELEKTRO-CARD %c v${IZKLOPI_CARD_VERSION} `, "color:#fff;background:#ff9800;font-weight:700", "color:#ff9800;background:#fff;font-weight:700");
