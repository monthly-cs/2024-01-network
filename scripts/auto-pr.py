import subprocess
import json
from typing import Tuple, Optional, TypedDict, List


class GitHubPr(TypedDict):
    number: int
    title: str


class GitHubPrTemplate(TypedDict):
    title: str
    body: str
    labelList: List[str]
    assigneeList: List[str]


def runnerWrapper(
    *,
    splitedCommand: List[str],
    encoding: str = 'utf-8'
) -> subprocess.CompletedProcess:
    return subprocess.run(splitedCommand,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          encoding=encoding)


def runner(
    *,
    command: str
) -> Tuple[bool, str, str]:

    result = runnerWrapper(splitedCommand=command.split(' '))
    isSuccess = result.stderr == ''

    return isSuccess, result.stdout, result.stderr


def splitRunner(
    *,
    splitedCommand: List[str]
):

    result = runnerWrapper(splitedCommand=splitedCommand)
    isSuccess = result.stderr == ''

    return isSuccess, result.stdout, result.stderr


def getPullRequestTemplate(
    *,
    base: str = 'main',
    head: str = 'dev'
):

    # [A] PR Commiter 생성
    splitedCommand = [
        'git', 'log',
        f'--pretty=format:%an',
        f'{base}..{head}'
    ]
    isSuccess, out, err = splitRunner(splitedCommand=splitedCommand)
    commiterList = list(set(out.split('\n')))

    # [B] PR Body 생성
    splitedCommand = [
        'git', 'log',
        f'--pretty=format:"| %ad | %h | %s | %an | %ae |"',
        f'--date=format-local:%y-%m-%d %H:%M',
        f'{base}..{head}'
    ]
    print("✅✅✅")
    print(splitedCommand)

    isSuccess, out, err = splitRunner(splitedCommand=splitedCommand)
    print("✅✅✅")
    print(out)

    pullRequestBody = f"""
[제목] [가제] 변경 필요
[기여자] {','.join(commiterList)}
[내용]

| 시간 | 커밋 ID | 커밋 제목 | 기여자 이름 | 기여자 Email |
| --------- | --------- | ---------- | ----------- | --------- |
"""
    commitList = out.split('\n')
    for commit in commitList:
        pullRequestBody += '\n' + commit[1:-1]
    print("✅✅✅")
    print(pullRequestBody)
    # PR Label 생성
    splitedCommand = [
        'git', 'log',
        f'--pretty=format:%s',
        f'--date=format-local:%y-%m-%d %H:%M',
        f'{base}..{head}'
    ]
    isSuccess, out, err = splitRunner(splitedCommand=splitedCommand)
    commitList = out.split('\n')

    tokenKeys = ['create', 'update', 'fix']
    tokenValues = ['enhancement', 'enhancement', 'bug']
    labelList = []
    for commit in commitList:
        for idx, tokenKey in enumerate(tokenKeys):
            hasToken = tokenKey in commit.lower()
            if hasToken:
                labelList.append(tokenValues[idx])
    labelList = list(set(labelList))

    githubPrTemplate: GitHubPrTemplate = {
        'title': '[가제] 변경 필요',
        'body': pullRequestBody,
        'labelList': labelList,
        'assigneeList': commiterList
    }

    return githubPrTemplate


def fetchGitHub(
    *,
    base: str = 'main',
    head: str = 'dev'
):
    command = 'git fetch origin main:main'
    isSuccess, outStr, errStr = runner(command=command)
    if not isSuccess:
        raise SyntaxError([
            'command syntax occure this error',
            errStr
        ])


def isExistsPrList(
    *,
    base: str = 'main',
    head: str = 'dev',
    jsonFormat: Optional[str] = None
) -> Tuple[bool, GitHubPr]:
    command = f'gh pr list --base {base} --head {head}'
    if jsonFormat:
        command += ' --json number,title'

    isSuccess, outStr, errStr = runner(command=command)
    if not isSuccess:
        raise SyntaxError([
            'command syntax occure this error',
            errStr
        ])

    prList: List[GitHubPr] = json.loads(outStr)
    hasPr = len(prList) != 0
    return hasPr, prList


def updatePullRequest(
    *,
    prList: List[GitHubPr],
    githubPrTemplate: GitHubPrTemplate
):
    pr = prList[0]

    title = githubPrTemplate['title']
    body = githubPrTemplate['body']
    labelList = githubPrTemplate['labelList']
    assigneeList = githubPrTemplate['assigneeList']

    splitedCommand = [
        'gh', 'pr', 'edit', str(pr['number']),
        '--title', str(title),
        '--body', f'"{body}"',
    ]

    TK = ','
    hasLabel = len(labelList) > 0
    if hasLabel:
        label = TK.join(labelList)
        splitedCommand.extend(['--add-label', label])

    hasAssignee = len(assigneeList) > 0
    if hasAssignee:
        assignee = TK.join(assigneeList)
        splitedCommand.extend(['--add-assignee', 'unchaptered'])

    isSuccess, outStr, errStr = splitRunner(splitedCommand=splitedCommand)
    print('outStr : ', outStr)
    print('errStr : ', errStr)


def createPullRequest(
    *,
    base: str,
    head: str,
    githubPrTemplate: GitHubPrTemplate
):

    title = githubPrTemplate['title']
    body = githubPrTemplate['body']
    labelList = githubPrTemplate['labelList']
    assigneeList = githubPrTemplate['assigneeList']

    # command = f'gh pr create --base {base} --head {head} --title {title} --body {body}'
    splitedCommand = [
        'gh', 'pr', 'create',
        '--base', base,
        '--head', head,
        '--title', title,
        '--body', body
    ]

    TK = ','
    hasLabel = len(labelList) > 0
    if hasLabel:
        label = TK.join(labelList)
        splitedCommand.extend(['--label', label])

    hasAssignee = len(assigneeList) > 0
    if hasAssignee:
        assignee = TK.join(assigneeList)
        splitedCommand.extend(['--assignee', assignee])

    isSuccess, outStr, errStr = splitRunner(splitedCommand=splitedCommand)
    print(isSuccess, outStr, errStr)


base = 'main'
head = 'dev'
# fetchGitHub(base=base,
#             head=head)
hasPr, prList = isExistsPrList(base=base,
                               head=head,
                               jsonFormat='number,title')
requestTemplate = getPullRequestTemplate(base=base,
                                         head=head)

if hasPr:
    updatePullRequest(prList=prList,
                      githubPrTemplate=requestTemplate)

else:
    createPullRequest(base=base,
                      head=head,
                      githubPrTemplate=requestTemplate)