# TOPOLOGÍA Y CONFIGURACIÓN DE RED (NETWORK_TOPOLOGY.md)

## 1. Topología Física y Lógica de Enlace

```
+---------------------------+                      +---------------------------+
|    HOST (Lenovo L480)     |                      |  TARGET (Raspberry Pi 5)  |
|                           |                      |                           |
| [Ethernet: Realtek GbE]   |<==== Direct Link ===>| [eth0: BCM54213PE GbE]    |
| IPv4: 169.254.184.179     |   (Cat 6 Ethernet)   | IPv4: Auto / DHCP         |
| IPv6: fe80::4c86:6ef6:... |                      | IPv6: fe80::4b3c:e19:...  |
|                           |                      |                           |
| [Wi-Fi 6 MT7921 5 GHz]    |<-- Access Point ---->| [wlan0: BCM43455 5 GHz]   |
| SSID: "LUANA 5G"          |   ("LUANA 5G")       | SSID: "LUANA 5G"          |
| IPv4: 192.168.100.11      |                      | IPv4: 192.168.100.x       |
+---------------------------+                      +---------------------------+
```

## 2. Estrategia de Acceso No Interactivo
* **Capa 2 / Capa 3 Primaria:** Enlace directo Ethernet con direccionamiento IPv6 Link-Local (`fe80::4b3c:e19:bb19:445a%20`) inmune a la ausencia de servidor DHCP.
* **Capa Wi-Fi Secundaria:** Conexión a la red inalámbrica `LUANA 5G` mediante NetworkManager (`nmcli`) para dotar a la Raspberry Pi de acceso a repositorios, NTP y salida a Internet (`8.8.8.8`).
* **Autenticación:** Llave criptográfica Ed25519 (`id_ed25519_hil`) sin contraseña asociada al usuario `alonso`.
