param(
  [string]$OutputPath = "research/Veridify_Pitch_Deck.pptx"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Escape-Xml {
  param([string]$Text)
  if ($null -eq $Text) { return "" }
  return [System.Security.SecurityElement]::Escape($Text)
}

function New-ParagraphXml {
  param([string]$Text, [int]$Level = 0, [int]$FontSize = 2200)
  $escaped = Escape-Xml $Text
  return @"
<a:p>
  <a:pPr lvl="$Level">
    <a:buChar char="-"/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" sz="$FontSize"/>
    <a:t>$escaped</a:t>
  </a:r>
  <a:endParaRPr lang="en-US" sz="$FontSize"/>
</a:p>
"@
}

function New-SlideXml {
  param(
    [string]$Title,
    [string[]]$Bullets
  )

  $titleXml = Escape-Xml $Title
  $paragraphs = New-Object System.Collections.Generic.List[string]
  foreach ($bullet in $Bullets) {
    $paragraphs.Add((New-ParagraphXml -Text $bullet))
  }
  $bodyXml = [string]::Join("`n", $paragraphs)

  return @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg>
      <p:bgPr>
        <a:solidFill>
          <a:srgbClr val="F7F5EF"/>
        </a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title 1"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="457200" y="274320"/>
            <a:ext cx="10972800" cy="914400"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0"/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" sz="2600" b="1"/>
              <a:t>$titleXml</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Accent Bar"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="457200" y="1234440"/>
            <a:ext cx="2743200" cy="137160"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="8C1D40"/></a:solidFill>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p/>
        </p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="4" name="Body 2"/>
          <p:cNvSpPr txBox="1"/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="457200" y="1600200"/>
            <a:ext cx="10972800" cy="4389120"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0">
            <a:spAutoFit/>
          </a:bodyPr>
          <a:lstStyle/>
          $bodyXml
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>
"@
}

$slides = @(
  @{
    Title = "1. Problem"
    Bullets = @(
      "AI-generated and manipulated images are now cheap, fast, and convincing.",
      "Veridify's project spec cites Nigerian insurance fraud as a costly trust problem, while most image review is still manual.",
      "Teams need a fast trust decision before approving claims, listings, or public-facing content."
    )
  },
  @{
    Title = "2. Target User"
    Bullets = @(
      "Primary user: insurance claims reviewers and fraud teams.",
      "Secondary users: marketplace trust teams, fact-checkers, and operations or compliance teams handling user-submitted images.",
      "Buyer: organizations that want an API-first verification layer instead of another disconnected dashboard."
    )
  },
  @{
    Title = "3. Solution Overview"
    Bullets = @(
      "Veridify is an AI-powered media verification product with a FastAPI backend and a Next.js frontend demo.",
      "The shipped flow already exists in code: create account, fund wallet, upload image, get verdict, review transaction history.",
      "Each verification returns a trust score, verdict, confidence, processing time, and signal breakdown."
    )
  },
  @{
    Title = "4. Squad API Integration"
    Bullets = @(
      "Squad is part of the core workflow, not a cosmetic payment add-on.",
      "Onboarding provisions a virtual account, funding generates a checkout flow, and the webhook confirms balance updates.",
      "Every verification deducts NGN 175 from the wallet so the money trail is visible throughout the demo."
    )
  },
  @{
    Title = "5. AI / Data Intelligence"
    Bullets = @(
      "The backend is already designed for three outcomes: AUTHENTIC, MANIPULATED, and SYNTHETIC.",
      "Today's build uses deterministic mock inference so the frontend, QA flow, and demo stay stable.",
      "The model contract is ready for a dual-branch system: EfficientNetB0 spatial analysis plus frequency-domain features with spatial and frequency score outputs."
    )
  },
  @{
    Title = "6. User Flow"
    Bullets = @(
      "The frontend implements a five-screen journey: onboarding, dashboard, verify, result, and transactions.",
      "Users create a workspace, top up a verification wallet, drag and drop an image, and receive a clear verdict screen.",
      "The result and transaction screens tie the AI decision directly to billing and audit history."
    )
  },
  @{
    Title = "7. Impact Potential"
    Bullets = @(
      "Veridify helps teams decide faster when a wrong image decision costs money, trust, or time.",
      "The first wedge is insurance fraud review, with the same engine reusable for marketplaces and fact-checking.",
      "Pitch assumption: 10,000 verifications per month at NGN 175 each equals NGN 1.75M in monthly gross verification revenue."
    )
  },
  @{
    Title = "8. Scalability & Business Model"
    Bullets = @(
      "Business model: pay-per-verification through a pre-funded Squad wallet.",
      "The architecture is API-first with stateless API keys, async backend services, cached repeat checks, and clear frontend/backend separation.",
      "The same engine can scale from this demo dashboard into partner APIs, internal trust tools, and future channels without changing the core verification flow."
    )
  },
  @{
    Title = "9. Research & Validation"
    Bullets = @(
      "The repo already shows implementation validation: webhook logging, rate limiting, balance tracking, transaction history, and QA test coverage for key flows.",
      "The product docs ground the idea in Nigerian fraud and manipulated-media risk.",
      "The honest next step is external validation: real model metrics, pilot users, and production threshold tuning."
    )
  },
  @{
    Title = "10. Team"
    Bullets = @(
      "Abdulmalik owns ML engineering and backend services.",
      "Peter owns the frontend experience and live demo flow; David owns QA and break-testing; Mathematician owns research and pitch support.",
      "Together, the team covers model logic, product UX, payments, validation, and storytelling."
    )
  }
)

$repoRoot = (Resolve-Path ".").Path
$outputFullPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputPath))
$outputDir = Split-Path -Parent $outputFullPath
if (-not (Test-Path $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$tempRoot = Join-Path $env:TEMP ("veridify-pptx-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

foreach ($relativePath in @(
  "_rels",
  "docProps",
  "ppt",
  "ppt/_rels",
  "ppt/slides",
  "ppt/slides/_rels",
  "ppt/slideLayouts",
  "ppt/slideLayouts/_rels",
  "ppt/slideMasters",
  "ppt/slideMasters/_rels",
  "ppt/theme"
)) {
  New-Item -ItemType Directory -Path (Join-Path $tempRoot $relativePath) | Out-Null
}

$now = [DateTime]::UtcNow.ToString("s") + "Z"
$slideContentOverrides = @(
  for ($i = 1; $i -le $slides.Count; $i++) {
    "  <Override PartName=`"/ppt/slides/slide$i.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slide+xml`"/>"
  }
) -join "`n"
$titleParts = @(
  foreach ($slide in $slides) {
    "      <vt:lpstr>$([System.Security.SecurityElement]::Escape($slide.Title))</vt:lpstr>"
  }
) -join "`n"
$slideIdXml = @(
  for ($i = 1; $i -le $slides.Count; $i++) {
    "    <p:sldId id=""$(256 + $i)"" r:id=""rId$($i + 1)""/>"
  }
) -join "`n"
$slideRelationshipXml = @(
  for ($i = 1; $i -le $slides.Count; $i++) {
    "  <Relationship Id=""rId$($i + 1)"" Type=""http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"" Target=""slides/slide$i.xml""/>"
  }
) -join "`n"

$contentTypes = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>
  <Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>
  <Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
$slideContentOverrides
</Types>
"@

$rootRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"@

$appXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office PowerPoint</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>$($slides.Count)</Slides>
  <Notes>0</Notes>
  <HiddenSlides>0</HiddenSlides>
  <MMClips>0</MMClips>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Slides</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>$($slides.Count)</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="$($slides.Count)" baseType="lpstr">
$titleParts
    </vt:vector>
  </TitlesOfParts>
  <Company>OpenAI Codex</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>
"@

$coreXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Veridify Pitch Deck</dc:title>
  <dc:subject>Squad Hackathon presentation</dc:subject>
  <dc:creator>OpenAI Codex</dc:creator>
  <cp:keywords>Veridify, PowerPoint, pitch deck</cp:keywords>
  <dc:description>Deck generated from the Veridify codebase and challenge slide order.</dc:description>
  <cp:lastModifiedBy>OpenAI Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">$now</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">$now</dcterms:modified>
</cp:coreProperties>
"@

$presentationXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                saveSubsetFonts="1" autoCompressPictures="0">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
$slideIdXml
  </p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr/>
    <a:lvl1pPr marL="0" indent="0"/>
    <a:lvl2pPr marL="457200" indent="0"/>
    <a:lvl3pPr marL="914400" indent="0"/>
  </p:defaultTextStyle>
</p:presentation>
"@

$presentationRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
$slideRelationshipXml
</Relationships>
"@

$slideMasterXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld name="Simple Master">
    <p:bg>
      <p:bgRef idx="1001">
        <a:schemeClr val="bg1"/>
      </p:bgRef>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="1" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle>
      <a:lvl1pPr algn="l">
        <a:defRPr sz="2600" b="1"/>
      </a:lvl1pPr>
    </p:titleStyle>
    <p:bodyStyle>
      <a:lvl1pPr marL="0" indent="0">
        <a:buChar char="•"/>
        <a:defRPr sz="2200"/>
      </a:lvl1pPr>
    </p:bodyStyle>
    <p:otherStyle>
      <a:defPPr/>
    </p:otherStyle>
  </p:txStyles>
</p:sldMaster>
"@

$slideMasterRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
"@

$slideLayoutXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             type="titleAndContent" preserve="1">
  <p:cSld name="Title and Content">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sldLayout>
"@

$slideLayoutRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
"@

$themeXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Veridify Theme">
  <a:themeElements>
    <a:clrScheme name="Veridify Colors">
      <a:dk1><a:srgbClr val="1F1F1F"/></a:dk1>
      <a:lt1><a:srgbClr val="F7F5EF"/></a:lt1>
      <a:dk2><a:srgbClr val="3D3D3D"/></a:dk2>
      <a:lt2><a:srgbClr val="FFFDFC"/></a:lt2>
      <a:accent1><a:srgbClr val="8C1D40"/></a:accent1>
      <a:accent2><a:srgbClr val="C18C5D"/></a:accent2>
      <a:accent3><a:srgbClr val="2F7D59"/></a:accent3>
      <a:accent4><a:srgbClr val="4E6E81"/></a:accent4>
      <a:accent5><a:srgbClr val="D9C5A1"/></a:accent5>
      <a:accent6><a:srgbClr val="6B5E62"/></a:accent6>
      <a:hlink><a:srgbClr val="8C1D40"/></a:hlink>
      <a:folHlink><a:srgbClr val="6B5E62"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Veridify Fonts">
      <a:majorFont>
        <a:latin typeface="Aptos Display"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Aptos"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Veridify Format">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:gradFill rotWithShape="1">
          <a:gsLst>
            <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="50000"/></a:schemeClr></a:gs>
            <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="50000"/></a:schemeClr></a:gs>
          </a:gsLst>
          <a:lin ang="5400000" scaled="0"/>
        </a:gradFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="lt1"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>
"@

$presPropsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentationPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>
"@

$viewPropsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:viewPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
          xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          lastView="sldView">
  <p:normalViewPr/>
  <p:slideViewPr/>
  <p:notesTextViewPr/>
  <p:gridSpacing cx="78028800" cy="78028800"/>
</p:viewPr>
"@

$tableStylesXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>
"@

[System.IO.File]::WriteAllText((Join-Path $tempRoot "[Content_Types].xml"), $contentTypes, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "_rels/.rels"), $rootRels, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "docProps/app.xml"), $appXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "docProps/core.xml"), $coreXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/presentation.xml"), $presentationXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/_rels/presentation.xml.rels"), $presentationRels, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/slideMasters/slideMaster1.xml"), $slideMasterXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/slideMasters/_rels/slideMaster1.xml.rels"), $slideMasterRels, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/slideLayouts/slideLayout1.xml"), $slideLayoutXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/slideLayouts/_rels/slideLayout1.xml.rels"), $slideLayoutRels, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/theme/theme1.xml"), $themeXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/presProps.xml"), $presPropsXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/viewProps.xml"), $viewPropsXml, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $tempRoot "ppt/tableStyles.xml"), $tableStylesXml, [System.Text.UTF8Encoding]::new($false))

for ($i = 0; $i -lt $slides.Count; $i++) {
  $slide = $slides[$i]
  $slideXml = New-SlideXml -Title $slide.Title -Bullets $slide.Bullets
  $slidePath = Join-Path $tempRoot ("ppt/slides/slide{0}.xml" -f ($i + 1))
  $slideRelPath = Join-Path $tempRoot ("ppt/slides/_rels/slide{0}.xml.rels" -f ($i + 1))
  [System.IO.File]::WriteAllText($slidePath, $slideXml, [System.Text.UTF8Encoding]::new($false))
  [System.IO.File]::WriteAllText($slideRelPath, @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>
"@, [System.Text.UTF8Encoding]::new($false))
}

if (Test-Path $outputFullPath) {
  Remove-Item -LiteralPath $outputFullPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempRoot, $outputFullPath)
Remove-Item -LiteralPath $tempRoot -Recurse -Force

Write-Output "Created $outputFullPath"
