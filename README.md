# Dual Stack IP Path comparison

Sub-project participating at the RIPE 72 Atlas Hackathon. The brother project
 compares the time required to establish a TCP connection against from all 
 RIPE Atlas probes with working dual stack against Alexa Top 100 sites with 
 dual stack support.
 
 
## Introduction

This tool uses some pre-prepared traceroutes from a small sample of 
dual-stack probes to a few dual-stack sites. Traceroutes are taken at nearly 
the same time for v4 and v6.

This project is self-contained, the data used is included.

## Screenshot

![Screen shot](/screenshot.png?raw=true)

## Usage

For the REST server that provides the data, run

```
python backend.py
```

For the Simple Web Server to access the webpage, execute

```
python -m SimpleHTTPServer 8000
```

And then visit

```
localhost:8000
```

## Caveats

* This is a proof of concept and some data has been crunched in advanced to 
make it fast.
* The display of RTT in the links is rather crude and can be made better.

