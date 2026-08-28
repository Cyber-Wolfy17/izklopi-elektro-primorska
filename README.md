# Izklopi Elektro Primorska

Home Assistant integracija, ki spremlja [načrtovane izklope električne energije](https://elektro-primorska.si/izklopi/) za poljubno lokacijo na območju **Elektra Primorska** in jih objavi kot senzorje.

## Kako deluje

Integracija periodično (privzeto vsakih 30 minut) prenese seznam napovedanih izklopov in ga filtrira glede na nastavljena **kraj** in **hišno številko**. Ustvari tri entitete:

<table>
  <thead>
    <tr>
      <th align="left">Entiteta</th>
      <th align="left">Tip</th>
      <th align="left">Opis</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>sensor.…_naslednji_izpad</code></td>
      <td><code>sensor</code>, <code>device_class: timestamp</code></td>
      <td>Časovni žig začetka naslednjega izklopa, oziroma <code>unknown</code>, če izklopa ni. Atributi: kraj, ulica, hišne številke, čas konca, tip akcije, število prihajajočih izklopov in njihov seznam (do 10).</td>
    </tr>
    <tr>
      <td><code>sensor.…_konec_izpada</code></td>
      <td><code>sensor</code>, <code>device_class: timestamp</code></td>
      <td>Časovni žig konca istega izklopa, oziroma <code>unknown</code>, če izklopa ni.</td>
    </tr>
    <tr>
      <td><code>binary_sensor.…_izpad_v_teku</code></td>
      <td><code>binary_sensor</code>, <code>device_class: problem</code></td>
      <td><code>ON</code>, ko smo trenutno znotraj termina izklopa (<code>od ≤ zdaj ≤ do</code>), sicer <code>OFF</code>. Stanje se preklopi točno ob uri začetka oziroma konca izklopa.</td>
    </tr>
  </tbody>
</table>

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

<table>
  <thead>
    <tr>
      <th align="left">Polje</th>
      <th align="left">Opis</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Kraj</td>
      <td>Npr. <code>Osp</code>. Ujema se s krajem ali imenom ulice.</td>
    </tr>
    <tr>
      <td>Hišna številka</td>
      <td>Neobvezno, npr. <code>1</code> ali <code>1000 a</code>. Če je prazno, se upoštevajo vsi izklopi za kraj.</td>
    </tr>
    <tr>
      <td>Območje</td>
      <td>Nadzorništvo Elektra Primorska (privzeto vsa).</td>
    </tr>
    <tr>
      <td>Interval posodabljanja</td>
      <td>Minute med osvežitvami (privzeto 30).</td>
    </tr>
  </tbody>
</table>

Nastavitve lahko kadarkoli spremeniš prek **Reconfigure** na kartici integracije.

## Primer obvestila

Avtomatizacija, ki pošlje obvestilo ob novem izklopu:

```yaml
alias: Obvestilo o izklopu elektrike
triggers:
  - trigger: state
    entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
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

## Primer avtomatizacij

Senzorja `naslednji_izpad` in `konec_izpada` sta časovna žiga, ki ju lahko uporabiš kot vir v časovnem triggerju (`trigger: time`) z nastavljivim `offset`. S tem se avtomatizacija sproži natanko N minut pred začetkom ali po koncu izklopa. Ko je senzor `unknown` (ni napovedanega izklopa), trigger preprosto počaka.

### TTS odštevanje pred izpadom

Avtomatizacija predvaja zvočno obvestilo 1 uro, 45, 30, 15 in 5 minut pred začetkom izklopa. Vsak trigger ima svoj `id`, ki ga sporočilo uporabi za število minut.

```yaml
alias: "TTS odštevanje pred izpadom"
triggers:
  - trigger: time
    id: "60"
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
      offset: "-01:00:00"
  - trigger: time
    id: "45"
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
      offset: "-00:45:00"
  - trigger: time
    id: "30"
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
      offset: "-00:30:00"
  - trigger: time
    id: "15"
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
      offset: "-00:15:00"
  - trigger: time
    id: "5"
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
      offset: "-00:05:00"
actions:
  - action: tts.say
    data:
      entity_id:
        - media_player.dnevna_soba
        - media_player.garaza
      message: >
        Pozor. Čez {{ trigger.id }} minut se začne napovedani izklop
        elektrike na naslovu
        {{ state_attr('sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad', 'ulica') }},
        {{ state_attr('sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad', 'kraj') }}.
mode: single
```

### Izklop avtomatik (npr. senčnikov) med izpadom

Avtomatizacija izklopi navedene avtomatike **1 uro in 5 minut pred** začetkom izklopa (prek `naslednji_izpad`) in jih spet vklopi **1 uro po koncu** izklopa (prek `konec_izpada`).

```yaml
alias: "Izklop senčnikov med izpadom"
triggers:
  - trigger: time
    id: izklopi
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_naslednji_izpad
      offset: "-01:05:00"
  - trigger: time
    id: vklopi
    at:
      entity_id: sensor.izklopi_elektro_primorska_vas_kraj_konec_izpada
      offset: "01:00:00"
conditions: []
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: izklopi
        sequence:
          - action: automation.turn_off
            target:
              entity_id:
                - automation.sencniki_glede_na_sonce
                - automation.pergola_glede_na_sonce
      - conditions:
          - condition: trigger
            id: vklopi
        sequence:
          - action: automation.turn_on
            target:
              entity_id:
                - automation.sencniki_glede_na_sonce
                - automation.pergola_glede_na_sonce
mode: single
```

> **Opomba:** Če se napoved izklopa prekliče po tem, ko so bile avtomatike že izklopljene, ostanejo izklopljene.

## Opombe

- Deluje samo za območje distributerja **Elektro Primorska d.d.**
- Podatki so neuradni; vir je spletna stran elektro-primorska.si.
- Integracija ne shranjuje zgodovine — senzorji vedno odražajo trenutno napovedane izklope.
- Težave in predlogi: [GitHub Issues](https://github.com/Cyber-Wolfy17/izklopi-elektro-primorska/issues).

## Licenca

[MIT](LICENSE)
