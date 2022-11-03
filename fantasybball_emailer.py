def espn_team_pull(year, leagueid):
    import requests
    import csv
    from datetime import datetime, timedelta
    import locale
    locale.setlocale( locale.LC_ALL, '' )
    currentdate = datetime.now()
    futuredate = currentdate + timedelta(days=7)

    url = "https://fantasy.espn.com/apis/v3/games/fba/seasons/" + str(year) + "/segments/0/leagues/" + str(leagueid)

    teamdata = requests.get(url).json()
    matchups = requests.get(url, params={"view": "mMatchup"}).json()

    teamMap = {}

    for team in teamdata['teams']:
        teamMap[team['id']] = team['location'] + " " + team['nickname']



    fullMap = {}

    for j in range(len(matchups['teams'])):
        player_list = []
        for i in range(len(matchups['teams'][j]['roster']['entries'])):
            player = matchups['teams'][j]['roster']['entries'][i]['playerPoolEntry']['player']['fullName']
            # if player[-3:] in ['Jr.', 'Sr.', 'III']:
            #     player = player[:-4]
            # elif player[-3:] == " II":
            #     player = player[:-3]
            # else:
            #     player = player
            player = player.replace(".","")
            player_list.append(player)
        fullMap[teamMap[j+1]] = player_list

    return fullMap

def add_salaries(team_map, salary_csv):
    import csv
    import unicodedata
    salary_dict = {}
    with open(salary_csv, newline='') as csvfile:
        salary_reader = csv.reader(csvfile, delimiter=',')
        for row in salary_reader:
            if row[1] == "Player":
                continue
            name = unicodedata.normalize('NFD', row[1]).encode('ascii', 'ignore').decode('UTF-8').replace(".", "")
            salary = row[3]
            salary_dict[name] = salary

    updated_team_dict = {}
    for team_name, player_list in team_map.items():
        tup_list = []
        for player in player_list:
            tup_list.append((player, salary_dict[player]))
        updated_team_dict[team_name] = tup_list

    return updated_team_dict

def send_email(overall_dict):
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, From
    from python_http_client.exceptions import HTTPError

    sg = SendGridAPIClient('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')

    html_content = ""
    for report_str_vals in overall_dict.values():
        html_content += report_str_vals

    message = Mail(
        to_emails="bryansback7@gmail.com",
        from_email=From("sumesharma1997@gmail.com", "Sumesh Sharma, the Commissioner"),
        subject="Test Email",
        html_content=html_content
        )
    print(message)
    try:
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return f"email.status_code={response.status_code}"
        #expected 202 Accepted

    except HTTPError as e:
        return e.message


def main():
    from datetime import datetime
    current_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    espn_team_map = espn_team_pull(2023, 1661951033)
    salary_map = add_salaries(espn_team_map, "nba_beta_salary.csv")
    overall_dict = {}
    for team_name, salary_list in salary_map.items():
        report_str = "Your team name is {team_name}. Below is a summary of your players as of {current_time}:<br><br>".format(team_name=team_name, current_time=current_time)
        running_total = 0
        for salary_tuple in salary_list:
            report_str += "Player: {player}, Salary: {salary}<br>".format(player=salary_tuple[0], salary=salary_tuple[1])
            running_total += int(salary_tuple[1][1:])
        running_total_dollar = '${:,.2f}'.format(running_total)
        report_str += "<br>Your total salary with these players is {running_total_dollar}".format(running_total_dollar=running_total_dollar)
        overall_dict[team_name] = report_str
        print(report_str)
    send_email(overall_dict)

if __name__ == "__main__":
    main()
