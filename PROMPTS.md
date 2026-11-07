# TrustVault – AI Development Log

This document records how AI tools were used during the development of TrustVault, the problems identified in suggested solutions, and the corrections made during development.

AI assistance was used for coding guidance, debugging, implementation suggestions and documentation. The developer reviewed the suggestions and tested application behavior.

## Entry 1 – Document Authorization and Permissions

**Date:** 5 November 2026

**AI tool:** ChatGPT

**Task / Prompt summary:** Asked for help implementing document access and edit permission checks for document owners and users receiving shared documents.

**AI output:** Suggested server-side permission helper functions to check document ownership and sharing permissions.

**Problem identified:** Some authorization behavior did not work as expected during manual testing. Requests returned HTTP 403 even in situations where access was expected.

**Correction and verification:** Reviewed the permission logic, document ownership and sharing records, and tested access using separate accounts. Updated the implementation and checked the affected routes.

**Related commit:** Add the actual Git commit link after committing this work.

## Entry 2 – TXT and PDF Document Editing

**Date:** 5 November 2026

**AI tool:** ChatGPT

**Task / Prompt summary:** Asked for guidance to implement direct TXT editing and PDF editing in TrustVault.

**AI output:** Suggested separate editing routes and templates for text and PDF documents, using PyMuPDF for PDF modification.

**Problem identified:** PDF editing required an appropriate library and correct handling of existing PDF content. Some initial editing approaches risked placing new text over existing content.

**Correction and verification:** Installed and checked PyMuPDF in the Python environment. Implemented separate editing routes and tested the PDF editor using a sample document.

**Related commit:** Add the actual Git commit link after committing this work.

## Entry 3 – PDF Text Placement Bug

**Date:** 7 November 2026

**AI tool:** ChatGPT

**Task / Prompt summary:** Asked for help correcting PDF editing because newly inserted text overlapped existing document content.

**AI output:** An initial suggestion inserted text at a fixed position near the top of the PDF.

**Problem identified:** Fixed-position insertion could overlap the existing heading or body content.

**Correction and verification:** Revised the approach to inspect existing text blocks and calculate a position below the existing content. Tested the revised PDF editor and observed that newly added text appeared below the existing content in the sample document. Previously inserted overlapping text remained in the test PDF.

**Related commit:** Add the actual Git commit link after committing this work.

## Entry 4 – View-Only and Edit Permission Testing

**Date:** 7 November 2026

**AI tool:** ChatGPT

**Task / Prompt summary:** Asked for guidance to test whether users with View Only permission could edit, replace or access restricted document operations.

**AI output:** Suggested testing document routes separately using accounts with different permissions.

**Problem identified:** Testing only the interface would not prove that the server prevented unauthorized requests.

**Correction and verification:** Performed manual authorization tests. The tested View Only requests to document replacement, TXT editing and PDF editing returned HTTP 403.

**Related commit:** Add the actual Git commit link after committing this work.

## Entry 5 – Document Replacement and Permission Preservation

**Date:** 7 November 2026

**AI tool:** ChatGPT

**Task / Prompt summary:** Asked for guidance to test document replacement and verify that existing sharing permissions were preserved.

**AI output:** Suggested replacing a shared document and checking its contents and permission records afterward.

**Problem identified:** Replacing a document should not unintentionally remove existing sharing permissions.

**Correction and verification:** Tested replacement using the Edit Access workflow. The shared document continued to display the existing Edit permission afterward. Further automated testing is still required.

**Related commit:** Add the actual Git commit link after committing this work.

## AI Usage Reflection

AI tools helped with implementation ideas, debugging and understanding Flask authorization behavior.

However, AI-generated suggestions were not accepted blindly. The developer reviewed the code, investigated unexpected behavior and tested changes using the local application.

One important example was the PDF text placement issue: the initial fixed-position approach could overlap existing content, so the implementation was revised and tested.

The final application should be evaluated based on its actual code, test results and demonstrated behavior.