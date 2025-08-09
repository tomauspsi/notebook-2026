check-availability
succeeded 1 minute ago in 10s
Search logs
1s
Current runner version: '2.327.1'
Operating System
Runner Image
Runner Image Provisioner
GITHUB_TOKEN Permissions
Secret source: Actions
Prepare workflow directory
Prepare all required actions
Getting action download info
Download immutable action package 'actions/checkout@v3'
Download immutable action package 'actions/setup-python@v4'
Complete job name: check-availability
0s
Run actions/checkout@v3
Syncing repository: tomauspsi/lenovo-t16-monitor
Getting Git version info
Temporarily overriding HOME='/home/runner/work/_temp/555cb4e2-34a6-4b61-bb6e-741545ebc45c' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/lenovo-t16-monitor/lenovo-t16-monitor
Deleting the contents of '/home/runner/work/lenovo-t16-monitor/lenovo-t16-monitor'
Initializing the repository
Disabling automatic garbage collection
Setting up auth
Fetching the repository
Determining the checkout info
Checking out the ref
/usr/bin/git log -1 --format='%H'
'c5a20dcdabce3d5d17b6e1a5460732de55da4ac4'
1s
4s
Run pip install requests beautifulsoup4
Collecting requests
  Downloading requests-2.32.4-py3-none-any.whl.metadata (4.9 kB)
Collecting beautifulsoup4
  Downloading beautifulsoup4-4.13.4-py3-none-any.whl.metadata (3.8 kB)
Collecting charset_normalizer<4,>=2 (from requests)
  Downloading charset_normalizer-3.4.2-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (35 kB)
Collecting idna<4,>=2.5 (from requests)
  Downloading idna-3.10-py3-none-any.whl.metadata (10 kB)
Collecting urllib3<3,>=1.21.1 (from requests)
  Downloading urllib3-2.5.0-py3-none-any.whl.metadata (6.5 kB)
Collecting certifi>=2017.4.17 (from requests)
  Downloading certifi-2025.8.3-py3-none-any.whl.metadata (2.4 kB)
Collecting soupsieve>1.2 (from beautifulsoup4)
  Downloading soupsieve-2.7-py3-none-any.whl.metadata (4.6 kB)
Collecting typing-extensions>=4.0.0 (from beautifulsoup4)
  Downloading typing_extensions-4.14.1-py3-none-any.whl.metadata (3.0 kB)
Downloading requests-2.32.4-py3-none-any.whl (64 kB)
Downloading charset_normalizer-3.4.2-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (148 kB)
Downloading idna-3.10-py3-none-any.whl (70 kB)
Downloading urllib3-2.5.0-py3-none-any.whl (129 kB)
Downloading beautifulsoup4-4.13.4-py3-none-any.whl (187 kB)
Downloading certifi-2025.8.3-py3-none-any.whl (161 kB)
Downloading soupsieve-2.7-py3-none-any.whl (36 kB)
Downloading typing_extensions-4.14.1-py3-none-any.whl (43 kB)
Installing collected packages: urllib3, typing-extensions, soupsieve, idna, charset_normalizer, certifi, requests, beautifulsoup4

Successfully installed beautifulsoup4-4.13.4 certifi-2025.8.3 charset_normalizer-3.4.2 idna-3.10 requests-2.32.4 soupsieve-2.7 typing-extensions-4.14.1 urllib3-2.5.0
0s
Run python scripts/check_lenovo.py
/home/runner/work/lenovo-t16-monitor/lenovo-t16-monitor/scripts/check_lenovo.py:4: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
=== Lenovo T16 Availability Check ===
Timestamp: 2025-08-09T04:34:46.560568
Scraper not implemented yet.
  print("Timestamp:", datetime.datetime.utcnow().isoformat())
0s
Post job cleanup.
0s
Post job cleanup.
/usr/bin/git version
git version 2.50.1
Temporarily overriding HOME='/home/runner/work/_temp/7dc7339f-cf37-4c5f-8425-6fe8919925ff' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/lenovo-t16-monitor/lenovo-t16-monitor
/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
http.https://github.com/.extraheader
/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
0s
Cleaning up orphan processes
