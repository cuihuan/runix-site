"""Content for the cross-cutting pages: /solutions and the six audience pages,
the Agents layer hub (/agents) and the roadmap (/roadmap).

tools/build_solutions.py renders them. Every statement here is written from what
the product pages, the docs and the legal pages already say; statuses come from
tools/stack.py at render time. No customer names, no numbers, no certifications,
no dates in the roadmap's forward-looking half (the shipped list carries the
dates the site already publishes).
"""

SOLUTIONS = [{'key': 'platform-teams',
  'slug': 'for-platform-teams',
  'name': 'Platform teams',
  'title': 'For Platform Teams: One Endpoint for Every Model | Runix',
  'description': 'How platform teams use Runix Router for key custody, per-key limits and mid-request '
                 'failover, and Runix FS where training data lives in object storage.',
  'h1': ['One endpoint for every model,', 'with the controls your team owns'],
  'sub': "For the team that owns the integration between the company's products and the model providers. "
         'Runix Router puts one OpenAI-compatible endpoint in front of every provider, with key custody, '
         'per-key limits and failover beneath it. Where training or inference data lives in object storage, '
         'Runix FS gives the GPUs a file system over the bucket.',
  'situation': [['Every team holds its own provider keys',
                 'Provider keys end up in repositories, CI variables and notebooks, one per team. Nobody can '
                 'say which key spent what, and revoking one means a redeploy. The platform team is asked to '
                 'fix this without breaking the teams that depend on it.'],
                ['A provider outage is your outage',
                 'When a provider degrades, every product that calls it directly degrades with it. Failover '
                 'written into each application is written differently each time, and a failure mid-stream '
                 "is the case nobody tested. The platform team ends up on call for other people's "
                 'integrations.'],
                ['The GPUs wait on the bucket',
                 'Training and inference data sits in object storage because that is where it is cheap. Jobs '
                 'then read it object by object, each framework with its own client for the same bucket, and '
                 'the GPUs wait while the data arrives.']],
  'stack': [['router',
             'One OpenAI-compatible endpoint in front of every provider, with keys held centrally: each key '
             'carries its quota, rate limits, allowed models and routing, revocable without a redeploy. '
             'Failover between providers fires mid-request, with streaming preserved.'],
            ['fs',
             'Where training or inference data lives in S3-compatible object storage, Runix FS mounts the '
             'bucket as a file system through FUSE, a Hadoop-compatible client or the Kubernetes CSI driver, '
             'with memory, SSD and HDD cache tiers on the workers. It runs in your own cloud account; the '
             'bucket keeps its layout and stays independently readable.']],
  'path': [['Tell us what you are building',
            'Send the models you call, the expected volume and what you need from the contract. Router is '
            'invite-only during early access; a person replies within one business day and sets the account '
            'up after a short intake.'],
           ['Evaluate before you pay',
            'Evaluation credits for Router are issued on request, with full functionality and no card '
            'required. Each key carries its own quota, limits and allowed models, and billing is itemised, '
            'so what each team spends is visible from the first request.'],
           ['Scope FS per deployment',
            'If the GPUs read from object storage, Runix FS is sized and deployed with you in your own AWS, '
            'Google Cloud or Azure account, and quoted per deployment during early access.']],
  'writing': [['Data terms',
               'Content sent through Runix Router is processed to serve the request and never used for '
               'training. Operational metadata is kept for billing and support.'],
              ['Contracting and billing',
               'You contract with Runix AI Inc; an MSA and a DPA are available on request. Billing is '
               'usage-based in USD, itemised, on a prepaid balance or by invoice.'],
              ['Statuses, literally',
               'Runix Router is in early access and running traffic, with no published SLA; the failover '
               'mechanism is documented instead. Runix FS is in early access, per deployment, and supported '
               'under contract.']],
  'reading': ['migrating-to-an-llm-gateway-without-downtime', 'streaming-llm-failover', 'per-key-llm-quotas'],
  'faq': [['Do we have to change our client code?',
           'Runix Router is OpenAI-compatible: chat completions and model listing, with server-sent events '
           'for streaming, behind an OpenAI-style error envelope with a request id on every response. You '
           'choose a model with an explicit id, or with auto.'],
          ['What happens when a provider fails mid-stream?',
           'Failover is provider to provider and fires mid-request, with streaming preserved. The mechanism '
           'is documented under Reliability; there is no published SLA during early access.'],
          ['Does Runix FS replace our object storage?',
           'No. In cache mode the bucket is the source of truth and writes pass through; in file-system mode '
           'operations complete in the cluster and then sync to the bucket. Paths map one-to-one to object '
           'keys, so the bucket stays independently readable.']],
  'cta': 'Put one endpoint in front of every provider'},
 {'key': 'model-teams',
  'slug': 'for-model-teams',
  'name': 'Model teams',
  'title': 'For Model Teams: Data, Fine-Tuning and Serving | Runix',
  'description': 'How teams that train or tune models use Runix Data for training sets with provenance, '
                 'Runix Models for open-weight tuning, and Runix FS to keep GPUs fed.',
  'h1': ['Data you can audit,', 'a model you can measure'],
  'sub': 'For teams that train or tune models and have to show where the data came from and whether the '
         'result beats what they run today. Runix Data builds training and evaluation sets with provenance '
         'per record. Runix Models fine-tunes open-weight models and serves them single-tenant. Runix FS '
         'reads it all from the bucket you already have.',
  'situation': [['Raw data that nobody can vouch for',
                 'Source material arrives duplicated, half-structured and with no record of its licence. A '
                 'near-duplicate that lands on both sides of a split inflates the score, and nobody notices '
                 'until the model ships. Cleaning it is a project of its own, and the rules differ by '
                 'field.'],
                ['A fine-tune with no baseline',
                 'A tuned model is only worth deploying if it beats the model you run today on your task. '
                 'Without a held-out set and a before-and-after comparison, the decision is a demo and a '
                 'feeling. Licence terms on the base model are checked last, if at all.'],
                ['Training jobs that wait on storage',
                 'The datasets live in object storage because that is where they are cheap to keep. Each '
                 'framework then brings its own way of reading the bucket, and the GPUs idle while the data '
                 'arrives.']],
  'stack': [['data',
             'Training and evaluation data in six domains, code first: every record carries its provenance '
             'and licence, personal data is masked before training and fails closed, and evaluation is split '
             'from training by source. Each delivery comes with a quality report: coverage, duplication, and '
             'what was dropped and why.'],
            ['pipeline',
             'The tooling Runix Data engagements run on: ingest, clean and dedupe, structure, mask, report, '
             'deliver, each stage leaving something you can inspect. Deduplication is exact, near and '
             'semantic, with counts you can check; it is in development with design partners.'],
            ['models',
             'Supervised fine-tuning, LoRA and QLoRA, and preference tuning with DPO on open-weight families '
             'such as Qwen, Llama, Mistral, Gemma and DeepSeek, licence checked first. The result is '
             'evaluated on a held-out set against the model you run today, and served single-tenant behind '
             'an OpenAI-compatible API.'],
            ['fs',
             'A file system over the S3-compatible bucket where the datasets live, mounted through FUSE, a '
             'Hadoop-compatible client or the Kubernetes CSI driver, with memory, SSD and HDD cache tiers. '
             'It runs in your own cloud account and the bucket stays independently readable.']],
  'path': [['Send a sample and the task',
            'A slice of the real data, not a description of it, and what the model has to do with the '
            'result: train on it, be evaluated on it, or both. We reply within one business day.'],
           ['Get a scoped plan and a quote',
            'Data engagements are priced per project or by volume and quoted before any work starts; the '
            'plan says which checks each record has to pass and what we think is not worth doing. Models '
            'engagements are quoted after scoping and before any training starts, with weights and access '
            'set in the contract.'],
           ['Train, evaluate, then serve',
            'Your data trains and evaluates the model you commission, and nothing else. Serving is dedicated '
            'and single-tenant, in your cloud account or on capacity arranged per engagement; Runix FS, if '
            'you use it, is sized and deployed with you.']],
  'writing': [['Data use',
               'The data you provide trains and evaluates the model you commission, and nothing else. Inputs '
               'are data you provide or have the rights to use, or public sources whose licences permit your '
               'use.'],
              ['Weights, access and pricing',
               'Weights and access are set in the engagement contract before training starts. Data is priced '
               'per project or by volume and Models per engagement, both quoted first; an MSA and a DPA are '
               'available on request.'],
              ['Statuses, literally',
               'Runix Data and Runix Models are in early access, by engagement, and Runix FS is in early '
               'access, per deployment. Runix Pipeline is in development with design partners.']],
  'reading': ['ai-data-pipelines', 'did-the-model-change-make-it-worse', 'introducing-runix-fs'],
  'faq': [['Do you clean our data or build new data?',
           'Both. Runix Data cleans and structures data you provide or have the rights to use, and builds '
           'task data, such as coding tasks verified by running their tests, to a scope agreed before work '
           'starts.'],
          ['How do you know the tuned model is better?',
           'It is evaluated on a task-specific held-out set, before and after, against the model you run '
           'today. Quantised variants are served only where that evaluation shows quality holds.'],
          ['Which base models can you tune?',
           'Open-weight families whose licences permit your use, for example Qwen, Llama, Mistral, Gemma and '
           'DeepSeek. The licence is checked before any training starts.']],
  'cta': 'Send a sample, and the task the model has to do'},
 {'key': 'engineering-orgs',
  'slug': 'for-engineering-orgs',
  'name': 'Engineering organisations',
  'title': 'For Engineering Organisations: AI Coding, Reviewed | Runix',
  'description': 'How engineering organisations adopt AI coding at scale with Runix Code, in development, '
                 'and Runix Router for model policy, per-key limits and attribution.',
  'h1': ['AI coding rolled out,', 'not smuggled in'],
  'sub': 'For organisations adopting AI coding across many developers and many repositories, where a pile of '
         'personal accounts and no visibility is the current state. Runix Code, in development, is being '
         'built so every change lands as a reviewable diff, with seats, per-key limits and attribution by '
         'developer. Runix Router gives the model calls one policy and one bill.',
  'situation': [['Personal accounts, no visibility',
                 'Developers sign up for assistants on their own, expense them or pay with their own cards, '
                 'and paste code into tools nobody reviewed. The organisation cannot say who uses what, on '
                 'which repositories, or what it costs. Turning that off loses the productivity; leaving it '
                 'on loses the audit.'],
                ['Agents that write without a reviewer',
                 'An agent that edits files silently is faster until the first bad change ships. Review '
                 'habits were built around diffs, and tools that bypass the diff bypass the review. Trust '
                 'has to be earned per change, not granted per tool.'],
                ['One provider key for the whole organisation',
                 'A single shared key means one runaway job empties the budget for everyone, and revoking it '
                 'means a redeploy. Which model serves which repository is decided by whoever wrote the '
                 'config last.']],
  'stack': [['code',
             'An AI coding agent being built for teams: grounded in your repository, with multi-file '
             'implement, refactor and test from one instruction, and every change landing as a reviewable '
             'diff, never a silent write. Seats, per-key limits and usage attribution by developer are part '
             'of the product, not an add-on; it is in development, with the waitlist open.'],
            ['router',
             "Optional in front of the agent's model calls, and useful on its own: one OpenAI-compatible "
             'endpoint with per-key quotas, rate limits and allowed models, revocable without a redeploy. '
             'Usage is billed in USD and itemised, so attribution survives the invoice.']],
  'path': [['Join the waitlist',
            "Tell us the team size, the repositories and what you want an agent to take off the team's "
            'plate. Cohorts are invited in order, and we reply within one business day with where the '
            'product is.'],
           ['Set up seats and policies',
            'Seats, per-key limits and review gates are configured with you. The team plans are set out on '
            'the Code plans page.'],
           ['Put Router in front, if you want one bill',
            'Runix Router accounts are set up after a short intake, with evaluation credits issued on '
            "request. Each key carries its quota, limits and allowed models, so the agent's model calls are "
            'governed the same way as every other call in the organisation.']],
  'writing': [['Data terms',
               'Content sent through Runix Router is processed to serve the request and never used for '
               'training; operational metadata is kept for billing and support. Put Router in front of the '
               'agent and its model calls are covered by the same terms.'],
              ['Contracting and billing',
               'You contract with Runix AI Inc; an MSA and a DPA are available on request. Router billing is '
               'usage-based in USD, itemised, on a prepaid balance or by invoice; Code has team plans, set '
               'out on the Code plans page.'],
              ['Statuses, literally',
               'Runix Code is in development and not generally available; its page describes what is being '
               'built, and waitlist cohorts are invited in order. Runix Router is in early access and '
               'running traffic, with no published SLA.']],
  'reading': ['llm-cost-attribution', 'llm-api-key-management', 'model-deprecation-without-a-redeploy'],
  'faq': [['Can developers use Runix Code today?',
           'No. It is in development and not generally available; the waitlist is open and cohorts are '
           'invited in order. The product page describes what is being built, not a shipped product.'],
          ['Does the agent commit code on its own?',
           'It is designed so that every change lands as a reviewable diff, never a silent write. Your '
           'review process stays where it is.'],
          ['How do we attribute cost to a team?',
           'Runix Code is designed with seats, per-key limits and usage attribution by developer. Runix '
           "Router meters per key, with itemised usage-based billing in USD, so a team's model spend is "
           'attached to its key at call time.']],
  'cta': 'Get your team into an early cohort'},
 {'key': 'studios',
  'slug': 'for-studios',
  'name': 'Studios and creators',
  'title': 'For Studios: Comic Dramas, Script to Episode | Runix',
  'description': 'How studios and creators of serialised visual stories use Runix Comic, an AI studio agent '
                 'in development, from script and storyboard to published episode.',
  'h1': ['A studio for comic dramas,', 'from script to episode'],
  'sub': 'For studios and independent creators making serialised visual stories, comic dramas in particular, '
         'where the work is the whole production line and not a single picture. Runix Comic, in development, '
         'is being built around pre-production, production and publishing, as an independent agent with its '
         'own harness. Runix Router is optional in front of its model calls.',
  'situation': [['Characters that drift between scenes',
                 'Image tools generate a panel at a time, and the same character comes back with a different '
                 'face in the next one. Keeping one look across an episode becomes manual work that the '
                 'tools were supposed to remove.'],
                ['Pictures are not an episode',
                 'A comic drama needs a script, an episode plan, storyboards, motion, voice, music and '
                 'subtitles before it is anything a platform will show. Stitching a chain of single-purpose '
                 'tools together is a production job in itself, and each handoff loses something.'],
                ['Publishing is where it breaks down',
                 'Each platform wants its own cut: vertical short videos for one, full episodes for another. '
                 'Re-cutting by hand for every platform is the last step, and the step most often skipped.']],
  'stack': [['comic',
             'An AI studio for comic dramas being built around the whole job: scripts, episode plans, '
             'character sheets that hold across scenes and storyboards in pre-production; styled panels that '
             'keep one look, motion and camera, AI voice-over, music and multi-language subtitles in '
             'production; vertical cuts and full episodes from one project, for the platforms you name. In '
             'development, waitlist open.'],
            ['router',
             "Optional in front of the agent's model calls: one OpenAI-compatible endpoint with keys, quotas "
             'and allowed models beneath it. The agent runs independently of it.']],
  'path': [['Join the waitlist',
            'Tell us what you make and where it is published. Cohorts are invited in order, and we reply '
            'within one business day with where the product is.'],
           ['Bring a script',
            'Cohorts start from a script, so pre-production, from episode plan to storyboard, is tried on '
            'your story and your characters rather than on a demo.'],
           ['Produce and publish from one project',
            'Production and publishing follow the same project: styled panels, motion, voice, music and '
            'subtitles, then vertical cuts and full episodes for the platforms you name.']],
  'writing': [['Data terms',
               "Where Runix Router sits in front of the agent's model calls, content is processed to serve "
               'the request and never used for training, and operational metadata is kept for billing and '
               'support.'],
              ['Contracting',
               'You contract with Runix AI Inc; an MSA and a DPA are available on request. There is no '
               'self-serve signup; accounts are set up after a short intake, and we reply within one '
               'business day.'],
              ['Statuses, literally',
               'Runix Comic is in development and not generally available; its page describes what is being '
               'built, and the waitlist is open. Runix Router is in early access, with no published SLA.']],
  'reading': ['how-to-make-a-comic-drama-with-ai',
              'comic-drama-vs-webtoon-vs-motion-comic',
              'llm-cost-control'],
  'faq': [['Is Runix Comic an image generator?',
           'No. It is an AI studio being built around the whole job: writing and boarding the story, '
           'producing the episode, and getting it published, as an independent agent with its own harness.'],
          ['Which platforms can it publish to?',
           'The product is designed to produce vertical short-video cuts and full episodes from one project, '
           'for the platforms you name.'],
          ['When can we use it?',
           'It is in development and not generally available. Join the waitlist with what you make and where '
           'it is published; cohorts are invited in order and we reply within one business day.']],
  'cta': 'Bring a script to the waitlist'},
 {'key': 'regulated-industries',
  'slug': 'for-regulated-industries',
  'name': 'Regulated industries',
  'title': 'For Regulated Industries: AI Your Reviewers Can Read | Runix',
  'description': 'How finance, legal and security teams use Runix: written data terms on Router, domain '
                 'rules for finance, legal and security data, and single-tenant serving.',
  'h1': ['Written answers', 'for the review that never ends'],
  'sub': 'For finance, legal and security teams that have to answer a reviewer before anything carries '
         'traffic. Runix Router puts the data terms, the contracting entity and the failover mechanism in '
         'writing. Runix Data applies domain rules for finance, legal and cybersecurity data. Runix Models '
         'serves a model single-tenant, in your cloud account, trained on your data and nothing else.',
  'situation': [['Where do the prompts go?',
                 'The first question in every review, and the one most teams cannot answer hop by hop. A '
                 "vendor's answer has to name the entity, the data terms and what is retained, in a document "
                 'the reviewer can file, not a slide.'],
                ['Data with rules of its own',
                 'Filings, contracts and vulnerability records each have a definition of clean that a '
                 'general-purpose pipeline does not know. Personal data has to be found and masked before '
                 'anything reaches a model, and a record that cannot be cleared has to be held back rather '
                 'than passed through.'],
                ['A shared model is a shared tenant',
                 'Fine-tuning on internal data raises the question of where the weights live and who else is '
                 'served from the same deployment. The honest answer has to be in the contract, before '
                 'training starts.']],
  'stack': [['router',
             'One OpenAI-compatible endpoint with central key custody and, per key, quotas, rate limits and '
             'allowed models. The data terms are written: content is processed to serve the request and '
             'never used for training, operational metadata is kept for billing and support, and a request '
             'id comes back on every response.'],
            ['data',
             'Domain data for finance, legal and cybersecurity, each with its own rules and the public '
             'standards they follow. Every record carries its provenance and licence; personal data is '
             'masked before a training set and detection fails closed; evaluation is split from training by '
             'source.'],
            ['models',
             'Fine-tuning of open-weight models, licence checked first, served dedicated and single-tenant '
             'behind an OpenAI-compatible API, in your cloud account or on capacity arranged per engagement. '
             'Your data trains and evaluates the model you commission, and nothing else; weights and access '
             'are set in the contract before training starts.']],
  'path': [['Bring the review to the intake',
            'Send what you are building, the expected volume and what the reviewers will ask for: the MSA '
            'and DPA, availability requirements, where data may travel. We reply within one business day and '
            'say plainly whether early access fits.'],
           ['Evaluate Router before paying',
            'Router accounts are set up after a short intake, with evaluation credits issued on request and '
            'no card required. Transport is TLS with the obsolete versions refused, and every response '
            'carries a request id.'],
           ['Scope Data and Models per engagement',
            'Data engagements are quoted per project or by volume before any work starts, with the checks '
            'each record has to pass written into the plan. Models engagements are quoted after scoping and '
            'before training, with weights, access and serving set in the contract.']],
  'writing': [['Data terms',
               'Content sent through Runix Router is processed to serve the request and never used for '
               'training, and operational metadata is kept for billing and support. The data you give Runix '
               'Models trains and evaluates the model you commission, and nothing else.'],
              ['Contracting and billing',
               'The contracting entity is Runix AI Inc; an MSA and a DPA are available on request. Billing '
               'is usage-based in USD, itemised, on a prepaid balance or by invoice.'],
              ['What is not claimed',
               'No service level is published during early access; the failover mechanism is documented '
               'instead. Where your procurement requires a guarantee, say so at intake and we will say '
               'plainly whether early access fits.']],
  'reading': ['where-your-prompts-actually-go', 'ai-vendor-data-questions', 'llm-gateway-security-review'],
  'faq': [['Can we sign an MSA and a DPA?',
           'Yes, on request. The contracting entity is Runix AI Inc, and the documents are reviewed per '
           'engagement.'],
          ['Is there a service level agreement?',
           "Not during early access. Runix Router's failover fires mid-request with streaming preserved, and "
           'the mechanism is documented; a published number would need a contract behind it.'],
          ['Is our data used to train anything?',
           'Content sent through Runix Router is never used for training. With Runix Models, your data '
           'trains and evaluates the model you commission, and nothing else; weights and access are fixed in '
           'the contract before training starts.']],
  'cta': "Bring your reviewers' questions to the intake"},
 {'key': 'research-labs',
  'slug': 'for-research-labs',
  'name': 'Research labs',
  'title': 'For Research Labs: Storage, Data and Models | Runix',
  'description': 'How AI for Science and embodied AI groups use Runix FS for datasets in buckets, Runix Data '
                 'for antibody, protein and embodied AI data, and Runix Models.',
  'h1': ['Datasets in the bucket,', 'GPUs that stop waiting'],
  'sub': 'For AI for Science and embodied AI groups with datasets in object storage and records that need '
         'domain judgement before a model learns from them. Runix FS mounts the bucket as a file system, '
         'cached in front of the GPUs. Runix Data applies its rules for antibody, protein and embodied AI '
         'records. Runix Models tunes and serves open-weight models.',
  'situation': [['The data is in a bucket, the job wants files',
                 'Sequence files, trajectories and sensor recordings sit in object storage because that is '
                 'where they fit. Training code wants a path, and each framework brings its own client for '
                 'the same bucket, so the GPUs wait while the data arrives.'],
                ['Records where a bad merge changes the answer',
                 'Antibody and protein records come from sources that disagree on identifiers, numbering and '
                 'format. Merging them carelessly changes the science, not just the formatting, and a '
                 'near-duplicate on both sides of a split inflates an evaluation.'],
                ['A tuned model with no baseline and no home',
                 "A model tuned on the group's data has to be compared with the model the group runs today, "
                 'on a held-out set, before anyone trusts it. It then needs somewhere to run that is not a '
                 'shared endpoint, with the licence on the base model checked first.']],
  'stack': [['fs',
             'An AI-native file system over the S3-compatible bucket where the datasets live: FUSE mount, '
             'Hadoop-compatible client, Java, Python and Rust SDKs, and a Kubernetes CSI driver, with '
             'memory, SSD and HDD cache tiers on the workers and metadata replicated with Raft. Built on '
             'Curvine, Apache-licensed and a CNCF Sandbox project; it runs in your own cloud account.'],
            ['data',
             'Domain data with its own rules for AI for Science, where the work is limited to biological '
             'data, antibody and protein records, and for embodied AI. Every record carries its provenance '
             'and licence, evaluation is split from training by source, and each delivery comes with a '
             'quality report.'],
            ['models',
             'Supervised fine-tuning, LoRA and QLoRA, and DPO on open-weight families whose licences permit '
             'your use, evaluated on a held-out set against the model you run today. Served dedicated and '
             'single-tenant, in your cloud account or on capacity arranged per engagement.']],
  'path': [['Tell us about the data',
            'Where it lives, roughly how big it is and what reads it, plus a sample of the records and what '
            'the model has to do with them. We reply within one business day.'],
           ['Get a scoped plan and a quote',
            'Runix FS is sized and deployed with you in your own AWS, Google Cloud or Azure account and '
            'quoted per deployment. Data is quoted per project or by volume and Models per engagement, both '
            'before any work starts.'],
           ['Mount, train, evaluate',
            'The bucket keeps its layout and stays independently readable, so nothing is migrated. Training '
            'and evaluation sets are split by source, and the tuned model is measured against the one you '
            'run today before it is served.']],
  'writing': [['Data use',
               'The data you provide to Runix Models trains and evaluates the model you commission, and '
               'nothing else. Inputs to Runix Data are data you provide or have the rights to use, or public '
               'sources whose licences permit your use.'],
              ['Where it runs',
               'Runix FS runs in your AWS, Google Cloud or Azure account, supported under contract with '
               'Runix AI Inc. Model serving is single-tenant, in your cloud account or on capacity arranged '
               'per engagement; an MSA and a DPA are available on request.'],
              ['Statuses, literally',
               'Runix FS is in early access, per deployment; Runix Data and Runix Models are in early '
               "access, by engagement. Performance figures on the FS page are the Curvine project's own "
               'measurements, labelled as such, not a Runix service level.']],
  'reading': ['introducing-runix-fs', 'ai-data-pipelines', 'rebuild-ai-unix'],
  'faq': [['Do we have to move the data out of the bucket?',
           'No. Paths map one-to-one to object keys, and the bucket keeps its layout and stays independently '
           'readable. In cache mode the bucket is the source of truth and writes pass through; in '
           'file-system mode operations complete in the cluster and then sync to the bucket.'],
          ['Which scientific data do you handle?',
           'Within AI for Science, biological data: antibody and protein records. Embodied AI is a separate '
           'domain with its own rules. For anything else, describe the data and we will say plainly whether '
           'we have the judgement for it.'],
          ['Can the tuned model run on our own cluster?',
           'Serving is dedicated and single-tenant, in your cloud account or on capacity arranged per '
           'engagement, behind an OpenAI-compatible API. Weights and access are set in the engagement '
           'contract before training starts.']],
  'cta': 'Tell us where the data lives'}]

AGENTS_HUB = {'title': 'Domain Agents: Software Engineering and Media | Runix',
 'description': 'The Agents layer of the Runix stack by domain: Runix Code for software engineering, Runix '
                'Comic for media, both in development, and which domains may follow.',
 'h1': ['One agent per domain,', 'two domains so far'],
 'sub': 'The top layer of the stack: independent agents, each built for one professional domain and run by '
        'its own harness. Today there are two: Runix Code for software engineering and Runix Comic for media '
        'and entertainment, both in development with waitlists open. The layer is presented the way a buyer '
        'thinks, by the work to be done.',
 'definition': [['What a domain agent is',
                 "A domain agent does the work of one profession, inside that profession's material: a "
                 'coding agent in a repository, a studio agent in a script and its episodes. It is '
                 'independent: it runs on its own and does not depend on the rest of the stack to do its '
                 'job. What it produces is something a person in that domain already knows how to review.'],
                ['What the harness is',
                 'The harness is what runs the agent: the loop that takes an instruction, plans the work, '
                 'calls the model, applies the result to the material and stops where a person has to look. '
                 'Each agent has its own, built for its domain, because the steps that make sense in a '
                 'repository are not the steps that make sense in an episode.'],
                ['Where the gateway sits',
                 "Runix Router is optional in front of an agent's model calls: one OpenAI-compatible "
                 'endpoint, with keys, quotas and allowed models beneath it. The agent runs independently of '
                 "it. Put Router in front when you want the agent's model usage governed and billed the same "
                 'way as every other call.']],
 'domains': [{'key': 'engineering',
              'name': 'Software engineering',
              'audience': 'Engineering teams',
              'product': 'code',
              'text': 'Runix Code is an AI coding agent being built for teams: grounded in your repository, '
                      'with multi-file implement, refactor and test from one instruction, and every change '
                      'landing as a reviewable diff. Seats, per-key limits and usage attribution by '
                      'developer are part of it. In development, waitlist open.'},
             {'key': 'media',
              'name': 'Media and entertainment',
              'audience': 'Studios and creators',
              'product': 'comic',
              'text': 'Runix Comic is an AI studio agent for comic dramas being built around the whole job: '
                      'scripts, episode plans, consistent characters and storyboards; styled panels, motion '
                      'and camera, voice, music and subtitles; vertical cuts and full episodes for the '
                      'platforms you name. In development, waitlist open.'}],
 'next': [['Finance',
           'The Data layer already has rules for finance data, with the public standards they follow. An '
           'agent for the domain would start from that same judgement; none is announced.'],
          ['Cybersecurity',
           'Cybersecurity is one of the six Data domains, with its own definition of a clean record. That '
           'judgement is the groundwork an agent would need; no agent is announced.'],
          ['Legal',
           'Legal data has its own rules in the Data layer, with the public standards they follow. An agent '
           'in this domain is a candidate for the same reason; nothing is scheduled.'],
          ['AI for Science',
           "The Data layer's work here is limited to biological data, antibody and protein records, with "
           'rules of its own. An agent would be a candidate only where that judgement is already in place; '
           'none is announced.']],
 'principles': [['Reviewable output',
                 "An agent's output is something a person in the domain reviews before it counts. Runix Code "
                 'is built so every change lands as a reviewable diff, never a silent write; the same rule '
                 'holds for every agent in the layer.'],
                ['Grounded in your material',
                 'Runix Code works from your repository: its modules, idioms and the versions you run. Runix '
                 'Comic works from your script, with characters that hold across scenes; neither starts from '
                 "a tutorial's example."],
                ['Team controls',
                 'Seats, per-key limits and usage attribution by developer, as Runix Code is being built '
                 'with, so an organisation can roll an agent out rather than discover it. The controls are '
                 'set up with you, not left to the honour system.'],
                ['Data terms in writing',
                 "Where Runix Router sits in front of an agent's model calls, its written data terms apply: "
                 'content processed to serve the request, never used for training. The contracting entity is '
                 'Runix AI Inc, with an MSA and a DPA on request.']],
 'faq': [['How many agents exist today?',
          'Two: Runix Code for software engineering and Runix Comic for comic dramas. Both are in '
          'development and not generally available; their waitlists are open.'],
         ['Does an agent need Runix Router?',
          'No. Each agent runs independently, with its own harness. Router is optional in front of its model '
          'calls, for teams that want one endpoint, per-key limits and one itemised bill.'],
         ['Will there be an agent for my domain?',
          "Nothing beyond Code and Comic is announced, and no dates are published. The Data layer's six "
          'domains are where the domain judgement already exists, and waitlist cohorts set the order of what '
          'gets built.']]}

ROADMAP = {'title': 'Runix Roadmap: What Is Live and What Comes Next | Runix',
 'description': 'The status of every Runix product, in literal terms: what early access and in development '
                'mean, what general availability adds, and how the order is decided.',
 'h1': ['Where Runix is,', 'and what comes next'],
 'sub': 'Seven products in five layers, at deliberately different stages. The statuses on this page are the '
        'ones used everywhere else on the site: Router, Models, Data and FS are in early access; Pipeline, '
        'Code and Comic are in development. What each status means, what general availability adds, and how '
        'the order is decided, without dates.',
 'now': 'Early access means a product you can use today, set up by the team rather than bought off a shelf. '
        'There is no self-serve signup: accounts and keys are issued after a short intake, and a reply comes '
        'within one business day. You evaluate before you pay: Runix Router issues evaluation credits on '
        'request with no card required, and Runix FS, Runix Data and Runix Models are scoped per engagement, '
        'with the plan and the price agreed before any work starts. No service level is published during '
        'early access; the failover mechanism is documented instead, and if your procurement needs a '
        'guarantee, say so at intake and we will say plainly whether early access fits.',
 'building': 'In development means the product page describes what is being built, not a shipped product. '
             'Runix Code and Runix Comic are built with waitlist cohorts, invited in order, who get access '
             'as capabilities land and whose feedback sets the order of what comes next. Runix Pipeline is '
             'built with design partners, the teams whose data runs through its stages first. None of the '
             'three is generally available, and nothing on their pages is a promise of a date.',
 'ga': [['A complete API reference',
         'A complete API reference ships with general availability; until then, onboarded teams get '
         'documentation and support directly from the engineers.'],
        ['A published service level for Router',
         'A service level for Runix Router is published at general availability, with a contract behind it; '
         'during early access the mechanism is documented and no number is.'],
        ['Self-serve signup and checkout',
         'Self-serve signup and checkout arrive with general availability; until then accounts and keys are '
         'set up by the team after a short intake.']],
 'principles': [['Statuses are literal',
                 'Early access and in development mean the same thing on every page of the site, and none of '
                 'them is aspirational. A product changes status when the thing changes, not when the copy '
                 'does.'],
                ['No dates are published',
                 'A date on a roadmap page is a promise the engineering has not made yet. The site says what '
                 'is running, what is being built and what general availability adds, and leaves the '
                 'calendar out.'],
                ['Cohorts set the order',
                 'Waitlist cohorts and design partners decide what lands next by what they run into. The '
                 'order follows their traffic and their data, not a launch plan.']],
 'status_line': {'early access': 'a team can be onboarded today, set up by us after a short intake, with '
                                 'evaluation or scoping before any payment',
                 'in development': 'the product page describes what is being built; it cannot be bought yet'},
 'ga_lede': 'General availability is a state, not a date. On this site it means these three things exist.',
 'products': {'code': ('Waitlist open. Cohorts are invited in order and get access as capabilities land; the '
                       'rollout guide describes seats, policies and the review-gated workflow.',
                       "Each cohort's feedback sets the order of what lands next. Team plans are set out on "
                       'the Code plans page as the shape of a future quote, not a current offer.'),
              'comic': ('Waitlist open. Cohorts start from a real script; the workflow guide says what you '
                        'bring and what the studio generates at each of the three stages.',
                        'Stages land in order: pre-production, production, publishing. What cohorts run into '
                        'shapes what lands next.'),
              'router': ('Running traffic. Accounts set up after a short intake; evaluation credits on '
                         'request with no card; one OpenAI-compatible endpoint, per-key limits, failover '
                         "mid-request, every model at its vendor's public list price.",
                         'General availability adds a complete API reference, a published service level with '
                         'a contract behind it, and self-serve signup and checkout.'),
              'models': ('By engagement. Base model, method, data, baseline and serving are agreed in '
                         'writing before any training starts; the tuned model is evaluated against the one '
                         'you run today.',
                         'The engagement guide on the product page is the current process. A productised '
                         'offer is not announced; engagements set what repeats.'),
              'data': ('By engagement. Six domains, code as the focus; a sample and a target task come in, a '
                       'scoped plan and a quote go back before any work starts; every delivery carries '
                       'provenance, licence and a quality report.',
                       'The six domain pages are built on public domain expertise today and are extended as '
                       'material is added. No dataset catalogue is announced.'),
              'pipeline': ('With design partners. The six stages run under every Runix Data engagement; the '
                           'engagement guide describes scoping, the stages and the quality report.',
                           'Pipeline is the tooling beneath Runix Data first. It is not sold on its own '
                           'today, and nothing on its page is a promise of when it will be.'),
              'fs': ('Deployed per customer. Sized and deployed with you in your own cloud account, built on '
                     'the open-source Curvine project; a quick start covers cluster, bucket, FUSE mount, CSI '
                     'and the cache.',
                     'An AWS Marketplace listing is in preparation. Early access continues as deployments '
                     "sized with you, in your account; the published figures stay the project's, not a Runix "
                     'service level.')},
 'shipped': [('July 8, 2026',
              'Runix announced; the gateway, now Runix Router, enters early access.',
              '/blog/introducing-runix', 'Introducing Runix'),
             ('August 2, 2026',
              'Documentation for every product: the Router quickstart with streaming, failover semantics and '
              'the error envelope with request ids.',
              '/docs/', 'The docs'),
             ('September 29, 2026',
              'Runix FS enters early access, built on the open-source Curvine project; the Security page is '
              'updated.',
              '/blog/introducing-runix-fs', 'Introducing Runix FS'),
             ('September 30, 2026',
              'Runix Models and Runix Data enter early access; the Router models catalogue at public list '
              'prices; the stack is drawn in five layers under the mission Rebuild AI Unix.',
              '/blog/rebuild-ai-unix', 'Rebuild AI Unix'),
             ('October 7, 2026',
              'Solutions by team, the Agents layer by domain, this roadmap, and the blog grouped by layer.',
              '/solutions', 'Solutions by team')],
 'faq': [('When will a product be generally available?',
          'No date is published for any product. The site states the status a product has reached and what '
          'general availability adds; a status changes when the thing changes.'),
         ('Can we use a product that is in development?',
          'Through its waitlist or as a design partner, in cohorts invited in order. Access arrives as '
          'capabilities land, and the product page says what is being built rather than what is finished.'),
         ('Does early access mean beta?',
          'It means set up by the team rather than bought off a shelf: a short intake, evaluation or scoping '
          'before any payment, and no published service level. The failover mechanism is documented instead '
          'of a number.')]}
