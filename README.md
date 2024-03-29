# amlen-prometheus-exporter

Amlen (ex Messagesight) Prometheus exporter

## Installing with Ansible (recommended option)

Go to [Ansible Role for amlen_exporter](https://github.com/heywood8/ansible-role-amlen_exporter) for instructions

## Installing from source

A step by step series of examples that tell you how to get exporter running as a service running

```shell
sudo yum install python3
git clone https://github.com/heywood8/amlen-prometheus-exporter.git
cd amlen-prometheus-exporter
pip3 install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
pyinstaller src/amlen_exporter.py --onefile
sudo mkdir -p /opt/amlen_exporter
sudo cp dist/amlen_exporter /opt/amlen_exporter
sudo useradd amlen_exporter
sudo cp examples/systemd/amlen_exporter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start amlen_exporter
sudo systemctl enable amlen_exporter
```

## Quickstart to run amlen-server (non-persistent)

docker run -p 9089:9089 -d --name imaserver -d heywood8/amlen-server:1.0.0.1-20220622.1025_eclipse
