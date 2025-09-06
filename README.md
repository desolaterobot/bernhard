# bernhard
SimplifyNext Agentic AI Hackathon

## Running steps for streamlit app:
1. Install dependencies.
```
pip install -r requirements.txt
```
2. Setup .env file with AWS model access keys
3. Run the streamlit app as localhost.
```
streamlit run app_agent.py
```
4. For error regarding "created_documents", just create a folder in your working directory with the same name for your own usage.
   
## Running steps for vector.py:
1. Install dependencies
```
pip install -r requirements.txt
```
2. Run the python file:
```
python vector.py
```
3. Move relevant documents to the documents folder.
4. Store text documents: type 's'
5. Query: type 'q'

Sample queries:
- Who is the joker?
- What did Heath Ledger do?
- Where did the last days of production take place?
- What is the general reception to The Dark Knight?

Initial findings: Works acceptably, but can be improved by using a better embedding model and better document splitting.

## Running steps for MCP server
0. Run the server:
```
python mcp_server.py
```
The server must be running if we want to use the tools.

1. Open GitHub copilot in VSCode
2. Change from Ask mode to Agent mode ('Ask' dropdown at the chat textbox), then change the model from GPT-4.1 to Claude Sonnet 3.5 (GPT is not good at tool calling)
3. Click on 'Configure Tools' (Screwdriver icon at chat textbox)
4. Click on 'Add MCP Server'  (MCP Logo icon on top)
5. Click on 'HTTP or server-side events
6. Enter 'http://127.0.0.1:4200/papers'
7. Enter any name as the server ID.
8. Select Global.
9. You should be redirected to an mcp.json file. If all goes well, you should see 
```
Running | Stop | Restart | N tools | More...
```
in the JSON. This means the server is running well and copilot has access to the tools.

10.   To confirm, go back to the Copilot window, then click on 'Configure Tools'. Scroll down and you should see the MCP server, followed by a list of functions in the server. This means that the tools are working.

### AWS SSO Login
1. Install AWS CLI https://awscli.amazonaws.com/AWSCLIV2.msi
2. Configure AWS SSO
`aws configure sso`
3. Fill in SSO information
```bash
SSO session name (Recommended): SimplifyNext
SSO start URL [None]: https://d-9667b91afb.awsapps.com/start
SSO region [None]: ap-southeast-1 
SSO registration scopes [sso:account:access]: sso:account:access
```
4. Login To AWS Account And Grant Access
5. Create SSO Profile Name
`Profile name: [Input]`
- Profile is stored in \.aws\config file
6. Obtain Temporary Credentials Via AWS SSO
`aws sso login --profile [profile name]`
- SSO Credentials Expiry Every 1-2hrs, have to re-run command
- Keys start with **AKIA** *(Persistent)*, configure in **~/.aws/credentials**
```ini
[SimplifyNext]
aws_access_key_id = AKIAxxxxxxxxxxxx
aws_secret_access_key = AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```
7. Access AWS SDK With Profile Name
```bash
aws sso login --profile YOUR_PROFILE
aws sts get-caller-identity --profile YOUR_PROFILE
```
- `get_caller_identity()`: is an STS(Security Token Service) API Call, it returns details about your AWS Identity that your current credentials represent.
- No need for storing of static API Keys in `.env` or other config files.
- Reduces risk of secret sprawling.
