# **Zumi Datenmonitor**
## **AKI Projektarbeit WS 2021/22**

### **Teammitglieder:**
Arian Braun, Florian Glauner, Jonas Holzner, Jan Sander

### **Betreuer:**
Prof. Dr.-Ing. Janis Keuper

---

## Ziel
In diesem Projekt soll ein "Daten-Monitor" für die Aufnahme und Selektion von Trainingsdaten in der Zumi-World erstellt werden.

## Aufgaben
1. Einarbeitung in die Zumi- und Zumi-World API
2. Untersuchung der Sensorik, erstellen einer API zum Auslesen der Sensordaten  
3. Implementierung eines „Random-Walk“ zur Aufnahme von Daten  
4. Aufbau eine Datenbank mit  Messdaten
5. Implementierung einer ML-gestützten Suchfunktion zum Finden ähnlicher Messpunkte

---

## Voraussetzungen:

- Zumi mit mind. Version **1.65** der offiziellen Zumibilbiothek [[pyPI](https://pypi.org/project/zumi/)]
- mind. Python **3.5.3** und folgende Pakete:
  - zumi
  - datetime
  - typing 
  - natsort == 7.1.1
  - fastdtw == 0.3.4
  - scipy == 1.7.3
  - numpy == 1.16.3
  - dtaidistance == 2.3.6
  - pymongo == 3.12.3
  - pyaml == 5.3.1

---

## Installation und Übersicht:

- Repository ins Zumi Homeverzeichnis klonen
- ggf. Konfigurationsdatei anpassen, in `/home/pi/zumi-datenmonitor/config.yml`
- Der Datenmonitor implemetiert verschiedene High-Level-Funktion, die interaktiv oder in Scripten zur vereinfachten Bedienung angesprochen werden können, siehe [Verfügbare Funktionen im Wiki](../wikis/Verfügbare-Funktionen)
- Klassendiagramm, siehe [Wiki](../../wikis/Klassendiagramm)
- Beispielhafte Jupyter Notebooks befinden sich im Ordner `examples/`

---

## Beispiel:

### Erstellen einer Sitzung:
```python
from data_monitor.zumi_data_monitor import *
from zumi.zumi import Zumi

zumi = Zumi()

# Vorkonfigurierte Sitzungsdaten laden
session = load_default_session(zumi)
start_recording(session)

# Sitzungsdaten aus Konfigurationsdatei einlesen
session = read_config("~/zumi-datenmonitor/config.yml", zumi)
start_recording(session)
```

### Starten des Random Walk:
```python
start_random_walk(zumi, timedelta(seconds=120))
```

### Übertragen der Logdateien in MongoDB:
```python
mongodb_uri = "mongodb://zumi:1234@127.0.0.1:27017/"
save_logs_to_database(log_path="/home/pi/zumi-datenmonitor/logs", mongodb_uri=mongodb_uri)
```

### Auslesen von Daten aus der MongoDB (vollständiger Code im Notebook):
```python
numeric_data = connection.get_numeric_sensor_data_by_time(
    datetime(2021, 11, 27, 19, 35),
    datetime(2021, 11, 27, 19, 36),
    {
        CollectionType.IR_DATA: ["ir_front_left", "ir_front_right", "timestamp"],
        CollectionType.MPU_DATA: [
            "gyro_x_angle",
            "gyro_y_angle",
            "gyro_z_angle",
            "timestamp",
        ],
    },
)
```

### Suchen nach ähnlichen Events (vollständiger Code im Notebook):
```python
result = search(
    SearchQuery(
        search_ts,
        datetime(2021, 11, 27, 19, 27),
        datetime(2021, 11, 27, 20, 5),
        timedelta(seconds=1),
        2,
        10,
    ),
    connection,
)
```
