import { Component, OnInit } from '@angular/core';

import { Router } from "@angular/router";

import { AuthService } from "../auth.service";

import {Md5} from 'ts-md5/dist/md5';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
},)
@Component({
  selector: 'logged',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
},)
export class LoginPage implements OnInit {

  constructor(private authService: AuthService, private router: Router) { }

  ngOnInit() {
  }

  login(form){
    var md5 = new Md5();
    let password_md5 = md5.appendStr(form.value.password).end();
    form.value.password = password_md5;
    this.authService.login(form.value).subscribe((res)=>{
      //this.router.navigateByUrl('home');
    })
  }

}
