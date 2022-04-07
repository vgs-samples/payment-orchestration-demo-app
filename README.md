# Payment Orchestration Sample Application
See this application in action by navigating to <https://payment-orchestration-sample.herokuapp.com/>

## Or, deploy it yourself
1. Send a request to VGS to create a Payment Orchestration tenant for one of your vaults

2. Create a gateway configuration using the configuration script:
[Gateway setup script](https://gist.github.com/mottersheadt/976b7f2418884fda2fc29dace2363b7b)

3. Deploy a new instance of the app:
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/mottersheadt/payment-orchestration-demo-app)

4. Upload Checkout.js yaml into your vault:
[inbound.yaml](https://github.com/mottersheadt/payment-orchestration-demo-app/blob/main/app/static/routes/inbound.yaml)

5. Update the "Upstream URL" on your new inbound route to point to your newly deployed version.

6. Navigate to your deployed version and perform a transaction.
