# Izklopi Elektro Primorska

Home Assistant integracija, ki spremlja [načrtovane izklope električne energije](https://elektro-primorska.si/izklopi/) za poljubno lokacijo na območju **Elektra Primorska** in jih objavi kot senzorje.

## Kako deluje

Integracija periodično (privzeto vsakih 30 minut) prenese seznam napovedanih izklopov in ga filtrira glede na nastavljena **kraj** in **hišno številko**. Ustvari tri entitete:

| Entiteta | Opis |
|---|---|
| `sensor.…_naslednji_izpad` | Časovni žig začetka naslednjega izklopa (`device_class: timestamp`), oziroma `unknown`, če izklopa ni. Atributi: kraj, ulica, hišne številke, čas konca, tip akcije, število prihajajočih izklopov in njihov seznam (do 10). |
| `sensor.…_konec_izpada` | Čas konca istega izklopa. |
| `binary_sensor.…_izpad_v_teku` | `ON`, ko smo trenutno znotraj termina izklopa (`od ≤ zdaj ≤ do`), sicer `OFF` (`device_class: problem`). Stanje se preklopi točno ob uri začetka oziroma konca izklopa. |

Podrobnosti iskanja:

- Kraj se ujema s podnizom v imenu kraja ali ulice.
- Hišna številka se primerja točno s seznamom prizadetih številk (npr. `1` ne ustreza `10`).
- Izklopi brez seznama hišnih številk se upoštevajo vedno, saj običajno prizadenejo celotno območje.

## Namestitev

### HACS (priporočeno)

1. V HACS dodaj ta repozitorij kot *Custom repository* (vrsta: Integration).
2. Poišči **Izklopi Elektro Primorska** in ga namesti.
3. Ponovno zaženi Home Assistant.

### Ročno

1. Kopiraj mapo `custom_components/izklopi_elektro_primorska` v `custom_components/` svoje Home Assistant namestitve.
2. Ponovno zaženi Home Assistant.

## Nastavitev

Nastavitve → Naprave in storitve → Dodaj integracijo → **Izklopi Elektro Primorska**:

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
    entity_id: sensor.izklopi_elektro_primorska_osp_1_naslednji_izpad
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
- Integracija ne shranjuje zgodovine — senzorji vedno odražajo trenutno napovedane izklope.
- Težave in predlogi: [GitHub Issues](https://github.com/Cyber-Wolfy17/izklopi-elektro-primorska/issues).

## Licenca

[MIT](LICENSE)
