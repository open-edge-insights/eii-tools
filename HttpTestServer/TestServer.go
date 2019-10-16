package main

import (
	"crypto/tls"
	"crypto/x509"
	"flag"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strconv"

	"github.com/golang/glog"
)

const (
	testServerCaPath   = "./cert.pem"
	testServerCertPath = "./cert.pem"
	testServerKeyPath  = "./key.pem"
	testClientCaPath   = "../../docker_setup/provision/Certificates/ca/ca_certificate.pem"
)

func main() {

	var devmode string
	var port string
	var host string
	flag.StringVar(&devmode, "dev_mode", "false", "devMode of external server")
	flag.StringVar(&port, "port", "8082", "port of external server")
	flag.StringVar(&host, "host", "localhost", "port of external server")

	flag.Parse()
	flag.Set("logtostderr", "true")
	http.HandleFunc("/metadata", responseServer)

	devMode, err := strconv.ParseBool(devmode)
	if err != nil {
		glog.Errorf("string to bool conversion error %s", err)
		os.Exit(1)
	}

	if devMode {
		err := http.ListenAndServe(host+":"+port, nil)
		if err != nil {
			glog.Errorf("%v", err)
			os.Exit(-1)
		}
	} else {

		// Create a CA certificate pool
		caCert, err := ioutil.ReadFile(testServerCaPath)
		if err != nil {
			glog.Errorf("%v", err)
		}
		caCertPool := x509.NewCertPool()
		caCertPool.AppendCertsFromPEM(caCert)

		caClientCert, err := ioutil.ReadFile(testClientCaPath)
		if err != nil {
			glog.Errorf("%v", err)
		}
		caClientCertPool := x509.NewCertPool()
		caClientCertPool.AppendCertsFromPEM(caClientCert)

		// Create the TLS Config with the CA pool and enable Client certificate validation
		tlsConfig := &tls.Config{
			RootCAs:    caCertPool,
			ClientCAs:  caClientCertPool,
			ClientAuth: tls.VerifyClientCertIfGiven,
		}
		tlsConfig.BuildNameToCertificate()

		// Create a Server instance to listen on port with the TLS config
		server := &http.Server{
			Addr:      host + ":" + port,
			TLSConfig: tlsConfig,
		}

		// Listen to HTTPS connections with the server certificate and wait
		err = server.ListenAndServeTLS(testServerCertPath, testServerKeyPath)
		if err != nil {
			glog.Errorf("%v", err)
			os.Exit(-1)
		}
	}
}

func responseServer(w http.ResponseWriter, r *http.Request) {

	switch r.Method {
	case "GET":
		fmt.Fprintf(w, "Received a GET request")
	case "POST":
		bodyBytes, err := ioutil.ReadAll(r.Body)
		if err != nil {
			glog.Errorf("Error reading request : %v", err)
		}
		metadata := string(bodyBytes)
		glog.Infof(metadata)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Received a POST request\n"))
	default:
		fmt.Fprintf(w, "Sorry, only GET and POST methods are supported.")
	}
}
