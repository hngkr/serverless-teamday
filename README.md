# serverless-teamday

## Requirements

`choco install awscli awssamcli python310`

`git clone https://github.com/hngkr/serverless-teamday.git` (eller fork, clone)

Til workshopping er det nemmeste, mest generiske (og farligste) at lave en bruger med en access-key i den rigtige konto.

For workshoppen: Sæt `region` op til `us-east-1` fordi der indgår CloudFront (indsæt gif af dumpsterfire & "Der må du aldrig gå hen, Simba!")

`aws configure --profile <profilename>`

Se evt: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html

Jeg har selv stor fornøjelse af Assume, men den nye AWS CLI er ikke helt så glemsom som den gamle: https://awsu.me/

# Hints

`$env:AWS_PROFILE = '<profilename>'`

`sam build --no-cached`

Vælg et stack-name som er unikt og genkendeligt i næste step:

`sam deploy --guided`

`aws s3 cp choices.json s3://<static-bucket-name>/choices.json`

`curl https://<cloudfront-distribution-domainname>/choices.json`
