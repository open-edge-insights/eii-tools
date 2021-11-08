/*
Copyright (c) 2021 Intel Corporation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

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
	"time"

	"github.com/golang/glog"
)

type testServer struct {
	tsCaCertPool   *x509.CertPool
	extCaCertPool  *x509.CertPool
	clientCert     tls.Certificate
	host           string
	port           string
	devMode        bool
	restExportPort string
	restExportHost string
}

const (
	testServerCaPath   = "./certificates/ca_cert.pem"
	testServerCertPath = "./certificates/server_cert.pem"
	testServerKeyPath  = "./certificates/server_key.pem"
	clientCaPath       = "../../build/provision/Certificates/ca/ca_certificate.pem"
)

// init is used to initialize and fetch required config
func (t *testServer) init() {

	var devmode string
	var port string
	var host string
	var restExportHost string
	var restExportPort string
	flag.StringVar(&devmode, "dev_mode", "false", "devMode of external server")
	flag.StringVar(&port, "port", "8082", "port of external server")
	flag.StringVar(&host, "host", "localhost", "host of external server")
	flag.StringVar(&restExportPort, "rdeport", "8087", "port of Rest Data Export server")
	flag.StringVar(&restExportHost, "rdehost", "localhost", "host of Rest Data Export server")

	flag.Parse()
	flag.Set("logtostderr", "true")

	// Setting host and port of Test Server
	t.host = host
	t.port = port
	t.restExportPort = restExportPort
	t.restExportHost = restExportHost

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
		// Create a Server instance to listen on port with the TLS config
		server := &http.Server{
			Addr:              t.host + ":" + t.port,
			ReadTimeout:       60 * time.Second,
			ReadHeaderTimeout: 60 * time.Second,
			WriteTimeout:      60 * time.Second,
			IdleTimeout:       60 * time.Second,
			MaxHeaderBytes:    1 << 20,
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
func (t *testServer) requestImage(imgHandle string) {

	// Timeout for every request
	timeout := time.Duration(60 * time.Second)

	if t.devMode {

		client := &http.Client{
			Timeout: timeout,
		}

		restExportDest := "http://" + t.restExportHost + ":" + t.restExportPort
		// Making a get request to rest server
		r, err := client.Get(restExportDest + "/image?img_handle=" + imgHandle)
		if err != nil {
			glog.Errorf("Remote HTTP server is not responding : %s", err)
		}

		if r != nil {
			// Read the response body
			defer r.Body.Close()
			response, err := ioutil.ReadAll(r.Body)
			if err != nil {
				glog.Errorf("Failed to receive response from server : %s", err)
			}
			glog.Infof("imgHandle %v and md5sum %v", imgHandle, md5.Sum(response))
		}
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

		restExportDest := "https://" + t.restExportHost + ":" + t.restExportPort
		// Making a get request to rest server
		r, err := client.Get(restExportDest + "/image?img_handle=" + imgHandle)
		if err != nil {
			glog.Errorf("Remote HTTP server is not responding : %s", err)
		}
		if r != nil {
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
	// Setting content type for encoding
	w.Header().Set("Content-type", "text/plain; charset=utf-8")

	switch r.Method {
	case "GET":
		fmt.Fprintf(w, "Received a GET request")
	case "POST":
		metadataBytes, err := ioutil.ReadAll(r.Body)
		if err != nil {
			glog.Errorf("Error reading request : %v", err)
		}
		// Fetching topic from metadata
		var metadataJSON map[string]interface{}
		json.Unmarshal(metadataBytes, &metadataJSON)

		imgHandle := fmt.Sprintf("%v", metadataJSON["img_handle"])
		glog.Infof("Received metadata : %v", metadataJSON)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Received a POST request\n"))
		if metadataJSON["img_handle"] != nil {
			// requesting image based on metadata obtained
			t.requestImage(imgHandle)
		}
	default:
		fmt.Fprintf(w, "Sorry, only GET and POST methods are supported.")
	}
}

func main() {
	t := new(testServer)
	t.init()
	t.startTestServer()

}
