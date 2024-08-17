**Design Docs**

Requirements For Notification:  
\[Simulating the notification system of a social media platform\]

- \`Like/Comment\` on a Post/Comment\[Reply is a type of comment\]  
  \[Make sure that there are no duplicates\]  
- \`Sending a Friend Request\` \-\> to the receiver of the request   
- \`Accepting the Friend Request\` \-\> to the sender  
- \`@mention\` in Post/Comment   
- \`Wants to be notified\` \<- for a particular user’s posts

Features:

- In-app notifications  
  - Switch: ON/OFF  
  - All the notifications of the same type within 5 minutes will be bundled  
  - Switch for all the above types of notifications:: want this type of notification or not  
- Mail notifications  
  - Switch: ON/OFF  
  - All the notifications of the same type within 60 minutes will be bundled  
  - Switch for all the above types of notifications:: want this type of notification or not

Components:

- Producers :: Features:  
  - modify the data received according to the format  
  - there will be a separation of concern for each producer  
  - the producers will push the objects in the Kafka  
- Kafka :: Features:  
  - Format \- JSON  
  - SCHEMA  
- Consumers :: Features:  
  - Perform database queries, to check the notification preference  
  - Bundling the notifications if necessary  
  - Discarding the notifications in necessary  
  - Retries if necessary  
  - Formatting if necessary  
  - Pushing to the queue  
  - Setting the priority according to the preference

Exposed Producers: 

- like\_on\_post\_or\_comment()

  parameter sample \- \`\`\`json{

  	action\_type: LIKE,

  action\_on: POST||COMMENT,

  action\_on\_id: POST\_ID||COMMENT\_ID,

  action\_by: USER\_ID,

  action\_at: timestamp

  }\`\`\`

- comment\_on\_post\_or\_comment() 

  parameter sample \- \`\`\`json{

  	type: COMMENT,

  	action\_data: “”,

  	action\_on: POST||COMMENT,

  action\_on\_id: POST\_ID||COMMENT\_ID,

  action\_by: USER\_ID,

  action\_at: timestamp

  }\`\`\`

- received\_friend\_request()

  parameter sample \- \`\`\`json{

  	type: FRIEND\_REQ,

  action\_by: USER\_ID,

  action\_on: USER\_ID,

  action\_at: timestamp

  }\`\`\`

- friend\_request\_accepted()

  parameter sample \- \`\`\`json{

  	action\_type: FRIEND\_REQ\_ACK,

  action\_by: USER\_ID,

  action\_on: USER\_ID,

  action\_at: timestamp

  }\`\`\`

- mentioned()

  parameter sample \- \`\`\`json{

  	action\_type: MENTION,

  action\_on: POST||COMMENT||CONVERSATION,

  action\_on\_id: POST\_ID||COMMENT\_ID||CONVERSATION\_ID,

  action\_by: USER\_ID,

  action\_at: timestamp

  }\`\`\`

Kafka Topics: \[Geographic partitioning will be used, but not for this simulation\]

- TOPIC   \[Replication\_factor\] \- n partitions \< (syntax)

	\[Manual Partition assignment\]

- LIKE              \[2\] \- 2 partitions : \[based on “action\_on”, POST/COMMENT\]  
- COMMENT    \[2\] \- 2 partitions : \[based on “action\_on”, POST/COMMENT\]  
- MENTION    \[3\] \- 3 partitions : \[based on “action\_on”, POST/COMMENT/CONVERSATIONS\]     
- NETWORKING \[2\] \- 2 partitions : \[based on “action\_type”\]

Kafka Consumers:

- Consumer\_Group\_SUB\_LIKE: 2 consumers  
- Consumer\_Group\_SUB\_COMMENTS: 2 consumers  
- Consumer\_Group\_SUB\_MENTION: 3 consumers  
- Consumer\_Group\_SUB\_NETWORKING: 2 consumers 

Middleware Utilities:

- database calls to ensure whether the notification will be sent or not  
- @mention and @connection will not be bundled  
  \[dynamic\] :: after 1st action, wait(15m/40s) \-\> 2nd action(12m/30s) \-\> 3rd action(8m/25s) and so on

	\[same target user\_id\]

- sms: like/comments will be bundled: 15mins wait time  
- in-app: like/comments will be bundled: 40s wait time  
- Bundle format: \`\`\`json{  
  			count: number,   
  			action\_by\_user\_id: string|string\[\],  
  			comment\_id: string|string\[\]|null,  
  			post\_id: string|string\[\]|null,

  }

In case of multiple hits, say (comment\_id \=\> \[\] &&  action\_by\_user\_id=\> \[\]) then pick the one with the max size.

Priority Message Queues:

- LIKE: 1 retry  
- COMMENT: 1 retry  
- MENTION: high\_priority : 2 retries  
- NETWORKING: 1 retry  
- DLQ: \#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#

User Schema:

- user\_id: string  
- in\_app\_notifications: boolean  
- mail\_notifications: boolean  
- mail\_like\_notifications: boolean  
- mail\_comment\_notifications: boolean  
- mail\_mention\_notifications: boolean  
- mail\_connection\_notifications: boolean

Schema Registry

Monitoring and Logging Targets

- end-to-end latency  
- Kafka processing latency  
- Database query latency  
- Notifications processed per sec  
- Rate of processing, retires, and dead letter queues  
- Cpu usage  
- Consumer lag  
- Bundling rate