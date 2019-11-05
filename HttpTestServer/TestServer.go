package main

import (
	"crypto/md5"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/golang/glog"
)

type testServer struct {
	tsCaCertPool  *x509.CertPool
	extCaCertPool *x509.CertPool
	clientCert    tls.Certificate
	host          string
	port          string
	devMode       bool
}

const (
	testServerCaPath   = "./cert.pem"
	testServerCertPath = "./cert.pem"
	testServerKeyPath  = "./key.pem"
	clientCaPath       = "../../docker_setup/provision/Certificates/ca/ca_certificate.pem"
)

// init is used to initialize and fetch required config
func (t *testServer) init() {

	var devmode string
	var port string
	var host string
	flag.StringVar(&devmode, "dev_mode", "false", "devMode of external server")
	flag.StringVar(&port, "port", "8082", "port of external server")
	flag.StringVar(&host, "host", "localhost", "port of external server")

	flag.Parse()
	flag.Set("logtostderr", "true")

	// Setting host and port of Test Server
	t.host = host
	t.port = port

	// Setting devMode
	devMode, err := strconv.ParseBool(devmode)
	if err != nil {
		glog.Errorf("string to bool conversion error %s", err)
		os.Exit(1)
	}
	t.devMode = devMode

	if !devMode {

		// Fetching and storing required CA certs
		testServercaCert, err := ioutil.ReadFile(testServerCaPath)
		if err != nil {
			glog.Errorf("%v", err)
		}

		caClientCert, err := ioutil.ReadFile(clientCaPath)
		if err != nil {
			glog.Errorf("%v", err)
		}

		// Adding required CA certs to certificate pool
		tsCaCertPool := x509.NewCertPool()
		tsCaCertPool.AppendCertsFromPEM(testServercaCert)

		extCaCertPool := x509.NewCertPool()
		extCaCertPool.AppendCertsFromPEM(caClientCert)

		t.tsCaCertPool = tsCaCertPool
		t.extCaCertPool = extCaCertPool

		// Read the key pair to create certificate struct
		cert, err := tls.LoadX509KeyPair(testServerCertPath, testServerKeyPath)
		if err != nil {
			glog.Errorf("Error : %s", err)
		}
		t.clientCert = cert
	}
}

// startTestServer starts an HTTP server to receive metadata
func (t *testServer) startTestServer() {

	http.HandleFunc("/metadata", t.responseServer)

	if t.devMode {
		err := http.ListenAndServe(t.host+":"+t.port, nil)
		if err != nil {
			glog.Errorf("%v", err)
			os.Exit(-1)
		}
	} else {

		// Create the TLS Config with the CA pool and enable Client certificate validation
		tlsConfig := &tls.Config{
			RootCAs:    t.tsCaCertPool,
			ClientCAs:  t.extCaCertPool,
			ClientAuth: tls.RequireAndVerifyClientCert,
		}
		tlsConfig.BuildNameToCertificate()

		// Create a Server instance to listen on port with the TLS config
		server := &http.Server{
			Addr:      t.host + ":" + t.port,
			TLSConfig: tlsConfig,
		}

		// Listen to HTTPS connections with the server certificate and wait
		err := server.ListenAndServeTLS(testServerCertPath, testServerKeyPath)
		if err != nil {
			glog.Errorf("%v", err)
			os.Exit(-1)
		}
	}
}

// requestImage is used to send GET requests
func (t *testServer) requestImage(metadata []byte) {

	// Timeout for every request
	timeout := time.Duration(10 * time.Second)

	// Fetching topic from metadata
	var metadataJSON map[string]interface{}
	json.Unmarshal(metadata, &metadataJSON)
	topic := fmt.Sprintf("%v", metadataJSON["topic"])

	// Request images only for streams containing results
	if strings.Contains(topic, "stream_results") {

		imgHandle := fmt.Sprintf("%v", metadataJSON["img_handle"])

		if t.devMode {

			client := &http.Client{
				Timeout: timeout,
			}

			// Making a get request to rest server
			r, err := client.Get("http://localhost:8087" + "/image?imgHandle=" + imgHandle)
			if err != nil {
				glog.Errorf("Remote HTTP server is not responding : %s", err)
			}

			// Read the response body
			defer r.Body.Close()
			response, err := ioutil.ReadAll(r.Body)
			if err != nil {
				glog.Errorf("Failed to receive response from server : %s", err)
			}
			glog.Infof("imgHandle %v and md5sum %v", imgHandle, md5.Sum(response))

		} else {

			// Create a HTTPS client and supply the created CA pool and certificate
			client := &http.Client{
				Transport: &http.Transport{
					TLSClientConfig: &tls.Config{
						RootCAs:      t.extCaCertPool,
						Certificates: []tls.Certificate{t.clientCert},
					},
				},
				Timeout: timeout,
			}

			// Making a get request to rest server
			r, err := client.Get("https://localhost:8087" + "/image?imgHandle=" + imgHandle)
			if err != nil {
				glog.Errorf("Remote HTTP server is not responding : %s", err)
			}

			// Read the response body
			defer r.Body.Close()
			response, err := ioutil.ReadAll(r.Body)
			if err != nil {
				glog.Errorf("Failed to receive response from server : %s", err)
			}
			// Print md5sum & imgHandle of received image
			glog.Infof("imgHandle %v and md5sum %v", imgHandle, md5.Sum(response))
		}
	}
}

// responseServer starts a server to receive POST requests
func (t *testServer) responseServer(w http.ResponseWriter, r *http.Request) {

	switch r.Method {
	case "GET":
		fmt.Fprintf(w, "Received a GET request")
	case "POST":
		metadataBytes, err := ioutil.ReadAll(r.Body)
		if err != nil {
			glog.Errorf("Error reading request : %v", err)
		}
		metadata := string(metadataBytes)
		glog.Infof("Received metadata : %s", metadata)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Received a POST request\n"))
		// requesting image based on metadata obtained
		t.requestImage(metadataBytes)
	default:
		fmt.Fprintf(w, "Sorry, only GET and POST methods are supported.")
	}
}

func main() {

	t := new(testServer)
	t.init()
	t.startTestServer()

}
