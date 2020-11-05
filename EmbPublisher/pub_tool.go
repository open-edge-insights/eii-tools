/*
Copyright (c) 2020 Intel Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

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
	eiscfgmgr "ConfigMgr/eisconfigmgr"
	eismsgbus "EISMessageBus/eismsgbus"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

var wg sync.WaitGroup

func main() {

	configmgr, err := eiscfgmgr.ConfigManager()
	if err != nil {
		fmt.Printf("Config Manager initialization failed...")
		return
	}

	appConfig, err := configmgr.GetAppConfig()
	if err != nil {
		fmt.Errorf("Error in getting application config: %v", err)
		return
	}

	pubctx, err := configmgr.GetPublisherByName(appConfig["pub_name"].(string))
	if err != nil {
		fmt.Printf("GetPublisherByName failed with error:%v", err)
		return
	}

	config, err := pubctx.GetMsgbusConfig()
	if err != nil {
		fmt.Printf("GetMsgbusConfig failed with error:%v", err)
		return
	}

	itr, err := appConfig["iteration"].(json.Number).Int64()
	if err != nil {
		fmt.Printf("-- Error in iteration conversion : %v\n", err)
		return
	}

	intval, err := time.ParseDuration(appConfig["interval"].(string))
	if err != nil {
		fmt.Printf("-- Error in interval conversion : %v\n", err)
		return
	}

	msg_file := "./datafiles/" + appConfig["msg_file"].(string)
	msg, err := eismsgbus.ReadJsonConfig(msg_file)
	if err != nil {
		fmt.Printf("-- Failed to parse config: %v\n", err)
		return
	}

	buffer, err := json.Marshal(msg)

	if err != nil {
		fmt.Printf("-- Failed to Marshal teh message : %v\n", err)
		return
	} else {
		fmt.Printf("-- message size is: %v\n", len(buffer))
	}

	topics, err := pubctx.GetTopics()
	if err != nil {
		fmt.Printf("Error: %v to GetTopics", err)
		return
	}

	for _, tpName := range topics {
		wg.Add(1)
		go publisher_function(config, tpName, buffer, intval, itr)
	}

	wg.Wait()
}

func publisher_function(config map[string]interface{}, topic string, buffer []byte, intval time.Duration, itr int64) {
	defer wg.Done()

	fmt.Printf("-- Initializing message bus context:%v\n", config)
	client, err := eismsgbus.NewMsgbusClient(config)
	if err != nil {
		fmt.Printf("-- Error initializing message bus context: %v\n", err)
		return
	}
	defer client.Close()

	fmt.Printf("-- Creating publisher for topic %s\n", topic)
	publisher, err := client.NewPublisher(topic)
	if err != nil {
		fmt.Printf("-- Error initializing publisher : %v\n", err)
		return
	}
	defer publisher.Close()

	for it := int64(0); it < itr; it++ {
		fmt.Printf("Topic Name:%v, Itr Num:%v\n", topic, it)
		err = publisher.Publish(buffer)
		if err != nil {
			fmt.Printf("-- Failed to publish message: %v\n", err)
			return
		}
		time.Sleep(intval)
	}
}
