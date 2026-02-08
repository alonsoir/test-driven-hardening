# 🤖 **PROMPT DE CONTINUIDAD - TDH ENGINE (VAGRANT EDITION)**

## 📋 **CONTEXTO DE SESIÓN ANTERIOR:**
**Fecha:** Sábado 8 de febrero, tarde frustrante  
**Tema:** Batalla épica contra Docker Desktop en macOS  
**Estado:** Docker Desktop 4.59.1 demostró ser software basura  
**Decisión histórica:** **NUNCA JAMÁS** usar Docker Desktop en macOS para desarrollo serio

## ⚠️ **LECCIÓN APRENDIDA (A SANGRE Y FUEGO):**
> "Docker Desktop en macOS es como construir un rascacielos sobre arena movediza. Nunca más."

## 🎯 **OBJETIVO DE LA PRÓXIMA SESIÓN:**
Migrar TODO el desarrollo del TDH Engine a un **entorno Vagrant Ubuntu 22.04** con Docker nativo (el de verdad, no la porquería de Docker Desktop).

---

## 🔧 **TAREAS CONCRETAS PARA COMENZAR:**

### **1. Crear estructura Vagrant limpia:**
```
engine-prototype/
├── vagrant/               # ← NUEVO: Todo lo de Vagrant
│   ├── Vagrantfile       # Configuración de la VM
│   └── provision/
│       ├── 01-base.sh    # Sistema base
│       ├── 02-docker.sh  # Docker NATIVO en Linux
│       ├── 03-tools.sh   # Herramientas SAST
│       └── 04-tdh.sh     # TDH Engine
└── (el resto igual)
```

### **2. Vagrantfile minimalista pero potente:**
```ruby
Vagrant.configure("2") do |config|
  # Ubuntu 22.04 LTS - ESTABLE como una roca
  config.vm.box = "ubuntu/jammy64"
  
  # Recursos para análisis pesados
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "8192"    # 8GB RAM - para LLMs
    vb.cpus = "4"         # 4 CPUs - para builds paralelos
  end
  
  # Sincronización de código (bidireccional, en vivo)
  config.vm.synced_folder "../", "/tdh-engine",
    type: "rsync",
    rsync__auto: true,
    rsync__args: ["--verbose", "--archive", "--delete", "-z"]
  
  # Provisionamiento en orden
  config.vm.provision "shell", path: "provision/01-base.sh"
  config.vm.provision "shell", path: "provision/02-docker.sh", privileged: true
  config.vm.provision "shell", path: "provision/03-tools.sh"
  config.vm.provision "shell", path: "provision/04-tdh.sh", privileged: false
end
```

### **3. Script de Docker NATIVO (el bueno):**
```bash
#!/bin/bash
# provision/02-docker.sh
echo "🐳 INSTALANDO DOCKER NATIVO EN LINUX (como Dios manda)"

# Método oficial - funciona SIEMPRE
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Sin Docker Desktop, sin problemas de socket, sin mierda de http+docker
sudo usermod -aG docker vagrant
sudo systemctl enable docker
sudo systemctl start docker

# Verificación
echo "✅ Docker version: $(docker --version)"
echo "✅ Docker info: $(docker info --format '{{.ServerVersion}}')"
echo "✅ Docker socket: /var/run/docker.sock (PERMISOS CORRECTOS)"
```

---

## 📊 **CRITERIOS DE ÉXITO PARA ESTA SESIÓN:**

### **✅ Objetivos mínimos (2 horas):**
- [ ] `vagrant up` completa sin errores
- [ ] VM Ubuntu 22.04 funcionando
- [ ] Docker nativo instalado y corriendo
- [ ] Sincronización de carpetas funcionando

### **🟡 Objetivos medios (4 horas):**
- [ ] TDH Engine instalado dentro de la VM
- [ ] Imagen `tdh-base:latest` construida dentro de la VM
- [ ] Análisis SAST funcionando en repositorio de prueba
- [ ] Contenedores Docker creándose sin errores

### **🟢 Objetivos completos (6+ horas):**
- [ ] Pipeline completo TDH funcionando 100% en VM
- [ ] Comandos `make` adaptados para usar VM
- [ ] Documentación para desarrollo en Vagrant
- [ ] Prueba end-to-end exitosa

---

## 🔗 **ARCHIVOS A CREAR:**

### **Nuevos:**
```
vagrant/Vagrantfile
vagrant/provision/01-base.sh
vagrant/provision/02-docker.sh
vagrant/provision/03-tools.sh
vagrant/provision/04-tdh.sh
vagrant/README-VAGRANT.md
```

### **Modificar:**
```
Makefile (añadir comandos vagrant-*)
README.md (añadir sección de desarrollo con Vagrant)
tdh_unified.py (posiblemente nada, debería funcionar igual)
```

---

## 🚨 **PUNTOS DE ATENCIÓN CRÍTICOS:**

### **1. Sincronización de carpetas:**
- RSync para cambios en caliente
- Excluir venv/, __pycache__/, etc.
- Mantener permisos correctos

### **2. Recursos de la VM:**
- Suficiente RAM para análisis SAST pesados
- CPUs para builds paralelos
- Swap adecuado si es necesario

### **3. Networking:**
- Forward de puertos si necesitamos API
- Acceso a internet para descargas
- Comunicación entre contenedores dentro de la VM

---

## 📝 **PROMPT DE INICIO PARA DEEPSEEK (MAÑANA):**

"Después de la experiencia traumática con Docker Desktop en macOS, hemos tomado la decisión sabia y profesional de migrar TODO el desarrollo del TDH Engine a un entorno Vagrant con Ubuntu 22.04 y Docker nativo.

**Contexto actual:** Tenemos un TDH Engine funcional pero atrapado en el infierno de Docker Desktop. Docker funciona en terminal pero el SDK de Python falla con `http+docker`.

**Objetivo inmediato:** Crear un entorno Vagrant 100% estable con:
1. Ubuntu 22.04 LTS
2. Docker nativo (apt install docker.io)
3. Python 3.11
4. Todas las herramientas SAST
5. Sincronización bidireccional con el host

**Tarea concreta:** 
1. Crear `vagrant/Vagrantfile` con configuración robusta
2. Crear scripts de provisionamiento que instalen Docker **NATIVO** (no Docker Desktop)
3. Configurar sincronización RSync para desarrollo en caliente
4. Adaptar los comandos `make` para trabajar con la VM

**Requisitos específicos:**
- Docker debe funcionar con `docker.from_env()` sin errores
- El socket `/var/run/docker.sock` debe tener permisos correctos
- La VM debe tener recursos suficientes (8GB RAM, 4 CPUs)
- Los cambios en host deben reflejarse automáticamente en guest

**Preguntas para guiar la implementación:**
1. ¿RSync o NFS para sincronización? (RSync es más simple)
2. ¿Instalar Docker via `get.docker.com` o `apt install docker.io`?
3. ¿Cómo manejar el entorno virtual Python dentro de la VM?
4. ¿Qué puertos forwardear para debugging?

**Comenzamos creando la estructura Vagrant y el primer script de provisionamiento base.**

**RECORDATORIO SACRO:** Esto es una migración **DE FUGA** de Docker Desktop. Jamás volveremos a esa basura."

---

## 🎪 **EJEMPLO DE FLUJO ESPERADO AL FINAL DE LA SESIÓN:**

```bash
# DESDE EL HOST (macOS):
cd engine-prototype/vagrant

# Levantar la VM (primera vez)
vagrant up

# Conectar
vagrant ssh

# DENTRO DE LA VM (Ubuntu 22.04):
cd /tdh-engine

# Todo funciona PERFECTO:
source venv/bin/activate
docker ps  # ← FUNCIONA
python -c "import docker; print(docker.from_env().ping())"  # ← DEVUELVE True

# Ejecutar TDH Engine:
python tdh_unified.py sast-orchestrated https://github.com/alonsoir/test-zeromq-c-.git

# Debería mostrar:
# ✅ Contenedor creado
# ✅ Análisis SAST completado
# ✅ Resultados guardados
```

---

## 📞 **PUNTOS DE DECISIÓN PARA CONSULTA:**

### **Decisiones de arquitectura Vagrant:**
1. ¿Box: `ubuntu/jammy64` oficial o `bento/ubuntu-22.04`?
2. ¿Sincronización: RSync (más simple) o NFS (más rápido)?
3. ¿Networking: NAT (más seguro) o bridge (más accesible)?
4. ¿Provisionamiento: shell scripts o Ansible?

### **Decisiones de configuración Docker:**
1. ¿Instalar Docker Compose V1 o V2?
2. ¿Configurar Docker para usar overlay2 driver?
3. ¿Añadir registry mirror para acelerar descargas?
4. ¿Configurar límites de recursos Docker dentro de la VM?

---

## 🎯 **MÉTRICA DE PROGRESO FINAL:**

Al final de esta sesión, deberíamos poder responder **SÍ** a:
- [ ] ¿Puedo hacer `vagrant up` y tener un entorno funcional en 15 mins?
- [ ] ¿Docker funciona NATIVAMENTE sin errores de socket?
- [ ] ¿El TDH Engine ejecuta análisis completos dentro de la VM?
- [ ] ¿Puedo desarrollar en macOS y ejecutar en Linux sin dolor?

---

## ⚠️ **JURAMENTO DE DESARROLLADOR:**

> "Juro solemnemente jamás volver a intentar usar Docker Desktop en macOS para desarrollo profesional. Acepto que Vagrant/VirtualBox/Linux-native-Docker es el camino correcto, verdadero y sensato."

---

**¿Mañana comenzamos con la migración a Vagrant?** Esta vez será diferente. Esta vez funcionará. 🚀💪