import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { catchError, map, of, switchMap } from 'rxjs';

import { PostMortemService } from '../../services/post-mortem/post-mortem';

@Component({
  selector: 'app-post-mortem',
  imports: [CommonModule],
  templateUrl: './post-mortem.html',
  styleUrl: './post-mortem.css',
})
export class PostMortem {
  private readonly route = inject(ActivatedRoute);
  private readonly postMortemService = inject(PostMortemService);

  readonly postMortem$ = this.route.paramMap.pipe(
    map((params) => params.get('runId')),
    switchMap((runId) =>
      runId ? this.postMortemService.getForRun(runId).pipe(catchError(() => of(null))) : of(null)
    )
  );
}