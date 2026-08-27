# Elektro Primorska — načrtovani izklopi

Home Assistant integracija, ki spremlja [načrtovane izklope električne energije](https://elektro-primorska.si/izklopi/) za poljubno lokacijo na območju **Elektra Primorska** in jih objavi kot senzor.

## Kako deluje

Integracija periodično (privzeto vsakih 30 minut) prenese seznam napovedanih izklopov in ga filtrira glede na nastavljena **kraj** in **hišno številko**. Senzor `Naslednji izpad` ima:

- **stanje** = časovni žig začetka naslednjega izklopa (`device_class: timestamp`), oziroma `unknown`, če izklopa ni,
- **atributi**: kraj, ulica, hišne številke, čas konca, tip akcije, število prihajajočih izklopov in njihov seznam (do 10).

Iskanje se ujema s podnizom v imenu kraja ali ulice, hišna številka pa se primerja točno s seznamom prizadetih številk (npr. `1` ne ustreza `10`). Izklopi brez seznama hišnih številk se upoštevajo vedno, saj običajno prizadenejo celotno območje.

## Namestitev

### HACS (priporočeno)

1. V HACS dodaj ta repozitorij kot *Custom repository* (vrsta: Integration).
2. Poišči **Elektro Primorska - planned outages** in ga namesti.
3. Ponovno zaženi Home Assistant.

### Ročno

1. Kopiraj mapo `custom_components/elektro_izpadi` v `custom_components/` svoje Home Assistant namestitve.
2. Ponovno zaženi Home Assistant.

## Nastavitev

Nastavitve → Naprave in storitve → Dodaj integracijo → **Elektro Primorska - načrtovani izklopi**:

| Polje | Opis |
|---|---|
| Kraj | Npr. `Osp`. Ujema se s krajem ali imenom ulice. |
| Hišna številka | Neobvezno, npr. `1` ali `1000 a`. Če je prazno, se upoštevajo vsi izklopi za kraj. |
| Območje | Nadzorništvo Elektra Primorska (privzeto vsa). |
| Interval posodabljanja | Minute med osvežitvami (privzeto 30). |

Nastavitve lahko kadarkoli spremeniš prek **Reconfigure** na kartici integracije.

## Primer obvestila

Avtomatizacija, ki pošlje obvestilo ob novem izklopu:

```yaml
alias: Obvestilo o izklopu elektrike
triggers:
  - trigger: state
    entity_id: sensor.elektro_izpadi_osp_1_naslednji_izpad
actions:
  - action: notify.mobile_app
    data:
      title: "Načrtovan izklop elektrike"
      message: >
        {{ state_attr(trigger.entity_id, 'ulica') }},
        {{ state_attr(trigger.entity_id, 'kraj') }}:
        od {{ states(trigger.entity_id) }}
        do {{ state_attr(trigger.entity_id, 'konec') }}
```

## Opombe

- Deluje samo za območje distributerja **Elektro Primorska d.d.**
- Podatki so neuradni; vir je spletna stran elektro-primorska.si.
- Integracija ne shranjuje zgodovine — senzor vedno odraža trenutno napovedane izklope.

---

# Elektro Primorska — planned power outages (English)

A Home Assistant integration that monitors [planned power outages](https://elektro-primorska.si/izklopi/) published by **Elektro Primorska** (Slovenia) for any location you choose, and exposes them as a sensor.

## How it works

The integration periodically (every 30 minutes by default) fetches the list of announced outages and filters it by the configured **place** and **house number**. The `Naslednji izpad` (next outage) sensor provides:

- **state** — timestamp of the next outage start (`device_class: timestamp`), or `unknown` when there is none,
- **attributes** — place, street, house numbers, end time, action type, count of upcoming outages and their list (up to 10).

Place matching is a substring search on place or street names; the house number is matched exactly against the list of affected numbers (e.g. `1` does not match `10`). Outages without a house-number list are always included, as they typically affect the whole area.

## Installation

### HACS (recommended)

1. Add this repository as a *Custom repository* (type: Integration) in HACS.
2. Search for **Elektro Primorska - planned outages** and install it.
3. Restart Home Assistant.

### Manual

1. Copy the `custom_components/elektro_izpadi` folder into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.

## Configuration

Settings → Devices & Services → Add Integration → **Elektro Primorska - načrtovani izklopi**:

| Field | Description |
|---|---|
| Kraj (Place) | E.g. `Osp`. Matched against place or street name. |
| Hišna številka (House number) | Optional, e.g. `1` or `1000 a`. If empty, all outages for the place are considered. |
| Območje (Area) | Elektro Primorska supervision district (default: all). |
| Update interval | Minutes between refreshes (default 30). |

You can change the settings at any time via **Reconfigure** on the integration card.

## Notification example

An automation that sends a notification when a new outage appears:

```yaml
alias: Power outage notification
triggers:
  - trigger: state
    entity_id: sensor.elektro_izpadi_osp_1_naslednji_izpad
actions:
  - action: notify.mobile_app
    data:
      title: "Planned power outage"
      message: >
        {{ state_attr(trigger.entity_id, 'ulica') }},
        {{ state_attr(trigger.entity_id, 'kraj') }}:
        from {{ states(trigger.entity_id) }}
        until {{ state_attr(trigger.entity_id, 'konec') }}
```

## Notes

- Works only for the **Elektro Primorska d.d.** distribution area.
- Unofficial data; the source is the elektro-primorska.si website.
- The integration keeps no history — the sensor always reflects the currently announced outages.

## License

[MIT](LICENSE)
