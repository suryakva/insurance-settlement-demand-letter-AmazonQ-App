#!/usr/bin/env python3

import aws_cdk as cdk

from setup.qapp_with_document_enrichment_stack import QAppWithDocumentEnrichmentStack


app = cdk.App()
QAppWithDocumentEnrichmentStack(app, "QAppWithDocumentEnrichmentStack")

app.synth()
